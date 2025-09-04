from flask import render_template, flash, redirect, url_for, request, jsonify, current_app, abort
from flask_login import current_user, login_required
from bartr import db
from bartr.models import Item, Category, Trade, TradeItem, Message, Review, Favorite, ItemPhoto, User, Flag, MessageImage, Notification, ReviewPhoto, malaysia_now
from bartr.main import main
from bartr.main.forms import ItemForm, TradeForm, MessageForm, ReviewForm, FlagForm
from bartr.auth.forms import MALAYSIA_STATES, MALAYSIA_CITIES
from werkzeug.utils import secure_filename
from sqlalchemy import func, desc, case, or_, and_
from sqlalchemy.orm import joinedload
import os
from datetime import datetime, timedelta
from bartr.utils import allowed_file
import threading
import time

def _send_rating_reminder_notifications(trade):
    """Send rating reminder notifications when a trade is completed."""
    # Send notification to sender
    sender_notification = Notification(
        user_id=trade.sender_id,
        type='rating_reminder',
        content=f"Trade completed! You have 30 days to rate your experience with {trade.receiver.username}. After 30 days, rating will no longer be available.",
        trade_id=trade.id
    )
    db.session.add(sender_notification)
    
    # Send notification to receiver  
    receiver_notification = Notification(
        user_id=trade.receiver_id,
        type='rating_reminder',
        content=f"Trade completed! You have 30 days to rate your experience with {trade.sender.username}. After 30 days, rating will no longer be available.",
        trade_id=trade.id
    )
    db.session.add(receiver_notification)

# Removed _send_trade_received_notification function - no longer needed

def _check_auto_completion():
    """Check and process trades that need auto-completion"""
    try:
        # Check for trades that need auto-completion (48 hours)
        now = malaysia_now()
        auto_complete_hours = 48
        auto_complete_minutes = auto_complete_hours * 60  # Convert to minutes for consistency
        
        current_app.logger.info(f"Starting auto-completion check at {now}")
        
        # Simplified approach: Get all accepted trades and filter in Python
        all_accepted_trades = Trade.query.filter(Trade.status == 'accepted').all()
        current_app.logger.info(f"Found {len(all_accepted_trades)} accepted trades to check")
        
        # Auto-complete trades if needed
        completed_any = False
        for trade in all_accepted_trades:
            current_app.logger.info(f"Checking trade {trade.id} - sender_completed: {trade.sender_completed}, receiver_completed: {trade.receiver_completed}")
            
            # Skip if both users have already completed
            if trade.sender_completed and trade.receiver_completed:
                current_app.logger.info(f"Trade {trade.id} already completed by both parties, skipping")
                continue
            
            # Check sender completion scenario
            if trade.sender_completed and not trade.receiver_completed and trade.sender_completed_at:
                time_diff = (now - trade.sender_completed_at).total_seconds() / 60  # Convert to minutes
                current_app.logger.info(f"Trade {trade.id}: Sender completed {time_diff:.2f} minutes ago")
                if time_diff >= auto_complete_minutes:
                    current_app.logger.info(f"Auto-completing trade {trade.id} for receiver")
                    trade.status = 'completed'
                    trade.completed_at = now
                    trade.auto_completed = True
                    trade.receiver_completed = True
                    trade.receiver_completed_at = now
                    notification = Notification(
                        user_id=trade.receiver_id,
                        type='trade_auto_completed',
                        content=f"The trade for {trade.requested_item.name} has been automatically marked as completed after 2 minutes.",
                        trade_id=trade.id
                    )
                    db.session.add(notification)
                    # Send rating reminder notifications
                    _send_rating_reminder_notifications(trade)
                    completed_any = True
                    
            # Check receiver completion scenario
            elif trade.receiver_completed and not trade.sender_completed and trade.receiver_completed_at:
                time_diff = (now - trade.receiver_completed_at).total_seconds() / 60  # Convert to minutes
                current_app.logger.info(f"Trade {trade.id}: Receiver completed {time_diff:.2f} minutes ago")
                if time_diff >= auto_complete_minutes:
                    current_app.logger.info(f"Auto-completing trade {trade.id} for sender")
                    trade.status = 'completed'
                    trade.completed_at = now
                    trade.auto_completed = True
                    trade.sender_completed = True
                    trade.sender_completed_at = now
                    notification = Notification(
                        user_id=trade.sender_id,
                        type='trade_auto_completed',
                        content=f"The trade for {trade.requested_item.name} has been automatically marked as completed after 2 minutes.",
                        trade_id=trade.id
                    )
                    db.session.add(notification)
                    # Send rating reminder notifications
                    _send_rating_reminder_notifications(trade)
                    completed_any = True
        
        if completed_any:
            db.session.commit()
            current_app.logger.info("Committed auto-completion changes")
        else:
            current_app.logger.info("No trades auto-completed in this check")
            
    except Exception as e:
        current_app.logger.error(f"Error in auto-completion: {str(e)}")
        db.session.rollback()

@main.context_processor
def utility_processor():
    def get_notification_count():
        if current_user.is_authenticated:
            return Notification.query.filter_by(
                user_id=current_user.id,
                is_read=False
            ).count()
        return 0
        
    def get_unread_message_count():
        if current_user.is_authenticated:
            return Message.query.filter_by(
                receiver_id=current_user.id,
                is_read=False
            ).count()
        return 0
        
    return dict(
        notification_count=get_notification_count(),
        unread_count=get_unread_message_count()
    )

@main.route('/')
@main.route('/index')
def index():
    # Check for auto-completion for authenticated users
    if current_user.is_authenticated:
        _check_auto_completion()
    
    page = request.args.get('page', 1, type=int)
    category_id = request.args.get('category', type=int)
    condition = request.args.get('condition')
    state = request.args.get('state')
    city = request.args.get('city')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    sort_by = request.args.get('sort', 'newest')
    
    # Base query with eager loading of favorites - exclude traded and accepted items
    subquery_requested = db.session.query(Trade.requested_item_id).filter(Trade.status.in_(['completed', 'accepted']))
    subquery_offered = db.session.query(TradeItem.item_id).join(Trade).filter(Trade.status.in_(['completed', 'accepted']))
    
    query = Item.query.filter_by(is_active=True).filter(
        ~Item.id.in_(subquery_requested),
        ~Item.id.in_(subquery_offered)
    )
    
    # Apply category filter if specified
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    # Apply condition filter if specified
    if condition:
        query = query.filter_by(condition=condition)
    
    # Apply state and city filters if specified
    if state and state.strip():
        query = query.join(User).filter(User.region == state)
        if city and city.strip():
            query = query.filter(User.city == city)
    
    # Apply price range filter
    if min_price is not None:
        query = query.filter(Item.estimated_value >= min_price)
    if max_price is not None:
        query = query.filter(Item.estimated_value <= max_price)
    
    # Get paginated items with favorites eagerly loaded
    if current_user.is_authenticated:
        query = query.outerjoin(Favorite).options(db.joinedload(Item.favorites))
    
    # Apply sorting
    if sort_by == 'oldest':
        query = query.order_by(Item.created_at.asc())
    elif sort_by == 'price_low':
        # Handle NULL values by putting them at the end
        query = query.order_by(case((Item.estimated_value.is_(None), 1), else_=0), Item.estimated_value.asc())
    elif sort_by == 'price_high':
        # Handle NULL values by putting them at the end
        query = query.order_by(case((Item.estimated_value.is_(None), 1), else_=0), Item.estimated_value.desc())
    else:  # newest (default)
        query = query.order_by(Item.created_at.desc())
    
    items = query.paginate(page=page, per_page=12, error_out=False)
    
    # Get all categories for the sidebar
    categories = Category.query.all()
    
    # Get states for the filter
    states = [state for state, _ in MALAYSIA_STATES if state]  # Exclude empty state option
    
    # Get cities for the selected state from predefined list
    cities = []
    if state and state in MALAYSIA_CITIES:
        cities = MALAYSIA_CITIES[state]
    
    return render_template('main/index.html', 
                         items=items, 
                         categories=categories,
                         states=states,
                         cities=cities,
                         current_state=state,
                         current_city=city,
                         current_category=category_id,
                         current_condition=condition)

@main.route('/item/new', methods=['GET', 'POST'])
@login_required
def new_item():
    # Check if user has set their location
    if not current_user.region or not current_user.city:
        flash('Please set your location in your profile before adding items.', 'warning')
        return redirect(url_for('auth.profile'))
    
    form = ItemForm()
    form.category.choices = [(c.id, c.name) for c in Category.query.all()]
    
    if form.validate_on_submit():
        item = Item(
            name=form.name.data,
            description=form.description.data,
            condition=form.condition.data,
            category_id=form.category.data,
            estimated_value=form.estimated_value.data,
            user_id=current_user.id
        )
        db.session.add(item)
        db.session.commit()
        
        # Handle photo uploads
        for index, photo in enumerate(form.photos.data):
            if photo:
                filename = secure_filename(photo.filename)
                # Create the full path for the upload directory
                upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'items', str(item.id))
                # Ensure the upload directory exists
                os.makedirs(upload_dir, exist_ok=True)
                # Create the full file path
                file_path = os.path.join(upload_dir, filename)
                # Save the file
                photo.save(file_path)
                
                photo_entry = ItemPhoto(item_id=item.id, photo_path=filename, order=index)
                db.session.add(photo_entry)
        
        db.session.commit()
        flash('Your item has been listed!', 'success')
        return redirect(url_for('main.item', item_id=item.id))
    
    return render_template('main/new_item.html', title='New Item', form=form)

@main.route('/item/<int:item_id>')
def item(item_id):
    item = Item.query.get_or_404(item_id)
    return render_template('main/item.html', item=item)

@main.route('/item/<int:item_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_item(item_id):
    item = Item.query.get_or_404(item_id)
    if item.user_id != current_user.id:
        abort(403)
    
    form = ItemForm()
    form.category.choices = [(c.id, c.name) for c in Category.query.all()]
    
    if form.validate_on_submit():
        item.name = form.name.data
        item.description = form.description.data
        item.condition = form.condition.data
        item.category_id = form.category.data
        item.estimated_value = form.estimated_value.data
        
        # Handle photo deletions
        photos_to_delete = request.form.getlist('deleted_photos')
        if photos_to_delete:
            for photo_id in photos_to_delete:
                photo = ItemPhoto.query.get(photo_id)
                if photo and photo.item_id == item.id:
                    file_path = os.path.join(current_app.root_path, 'static', 'uploads', 'items', str(item.id), photo.photo_path)
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    db.session.delete(photo)
        
        # Handle photo reordering
        photo_orders = request.form.getlist('photo_order')
        if photo_orders:
            for order_data in photo_orders:
                if ':' in order_data:
                    photo_id, new_order = order_data.split(':', 1)
                    try:
                        photo_id = int(photo_id)
                        new_order = int(new_order)
                        photo = ItemPhoto.query.filter_by(id=photo_id, item_id=item.id).first()
                        if photo:
                            photo.order = new_order
                    except (ValueError, TypeError):
                        current_app.logger.warning(f"Invalid photo order data: {order_data}")
        
        # Handle new photos
        if form.photos.data:
            # Get the highest existing order number
            max_order = db.session.query(func.max(ItemPhoto.order)).filter_by(item_id=item.id).scalar() or 0
            
            for photo in form.photos.data:
                if photo.filename:
                    filename = secure_filename(photo.filename)
                    photo_path = os.path.join(current_app.root_path, 'static', 'uploads', 'items', str(item.id))
                    os.makedirs(photo_path, exist_ok=True)
                    photo.save(os.path.join(photo_path, filename))
                    max_order += 1
                    item_photo = ItemPhoto(item_id=item.id, photo_path=filename, order=max_order)
                    db.session.add(item_photo)
        
        db.session.commit()
        flash('Your item has been updated!', 'success')
        return redirect(url_for('main.item', item_id=item.id))
    
    elif request.method == 'GET':
        form.name.data = item.name
        form.description.data = item.description
        form.condition.data = item.condition
        form.category.data = item.category_id
        form.estimated_value.data = item.estimated_value
    
    return render_template('main/edit_item.html', title='Edit Item', form=form, item=item)

@main.route('/item/<int:item_id>/delete')
@login_required
def delete_item(item_id):
    item = Item.query.get_or_404(item_id)
    if item.user_id != current_user.id:
        flash('You cannot delete this item.', 'danger')
        return redirect(url_for('main.item', item_id=item.id))
    
    item.is_active = False
    db.session.commit()
    flash('Your item has been deleted.', 'success')
    return redirect(url_for('main.index'))

@main.route('/trade/new/<int:item_id>', methods=['GET', 'POST'])
@login_required
def new_trade(item_id):
    item = Item.query.get_or_404(item_id)
    if item.user_id == current_user.id:
        flash('You cannot trade with yourself.', 'danger')
        return redirect(url_for('main.item', item_id=item.id))
    
    form = TradeForm()
    # Filter out traded items from user's available items
    available_items = []
    for i in current_user.items:
        if i.is_active and not i.is_traded:
            available_items.append((i.id, i.name))
    form.offered_items.choices = available_items
    
    if form.validate_on_submit():
        try:
            # Log the form data
            current_app.logger.info(f"Form data received - offered_items: {form.offered_items.data}")
            
            # Get offered items
            offered_items = Item.query.filter(Item.id.in_(form.offered_items.data)).all()
            current_app.logger.info(f"Found {len(offered_items)} offered items in database")

            # Create the trade
            trade = Trade(
                sender_id=current_user.id,
                receiver_id=item.user_id,
                requested_item_id=item.id,
                message=form.message.data,
                status='pending'  # Explicitly set status
            )
            db.session.add(trade)
            db.session.flush()  # Get trade.id without committing
            current_app.logger.info(f"Created trade with ID: {trade.id}")
            
            # Add offered items to the trade
            for offered_item_id in form.offered_items.data:
                trade_item = TradeItem(trade_id=trade.id, item_id=offered_item_id)
                db.session.add(trade_item)
                current_app.logger.info(f"Added trade item: {offered_item_id} to trade {trade.id}")
            
            # Create a message about the trade
            trade_message = (
                f"🔄 Trade Proposal Requesting: {item.name}\n"
                f"Offering: {', '.join(i.name for i in offered_items)}"
            )
            
            # Send trade proposal message
            trade_proposal = Message(
                sender_id=current_user.id,
                receiver_id=item.user_id,
                content=trade_message,
                is_read=False
            )
            db.session.add(trade_proposal)
            
            # Create notification for trade proposal
            notification = Notification(
                user_id=item.user_id,
                type='trade_proposal',
                content=f"{current_user.username} has sent you a trade proposal for {item.name}",
                trade_id=trade.id,
                item_id=item.id
            )
            db.session.add(notification)
            
            # Removed trade received notification - keeping only the trade proposal notification above
            
            # Send user's message separately if provided
            if form.message.data:
                user_message = Message(
                    sender_id=current_user.id,
                    receiver_id=item.user_id,
                    content=form.message.data,
                    is_read=False
                )
                db.session.add(user_message)
            
            db.session.commit()
            current_app.logger.info("Successfully committed trade to database")
            flash('Your trade proposal has been sent!', 'success')
            return redirect(url_for('main.my_trades', status='pending_approval'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating trade: {str(e)}")
            flash('An error occurred while creating the trade. Please try again.', 'danger')
            return redirect(url_for('main.new_trade', item_id=item.id))
    
    return render_template('main/new_trade.html', form=form, item=item)

@main.route('/trade/<int:trade_id>/<string:action>', methods=['GET', 'POST'])
@login_required
def trade_action(trade_id, action):
    trade = Trade.query.get_or_404(trade_id)
    
    # Check if this is an AJAX request
    is_ajax = request.headers.get('Content-Type') == 'application/json' or request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    # Check if user is either the sender or receiver
    if trade.sender_id != current_user.id and trade.receiver_id != current_user.id:
        if is_ajax:
            return jsonify({'success': False, 'message': 'You cannot perform this action.'}), 403
        flash('You cannot perform this action.', 'danger')
        return redirect(url_for('main.my_trades'))
    
    # Only receiver can accept or reject
    if action in ['accept', 'reject'] and trade.receiver_id != current_user.id:
        if is_ajax:
            return jsonify({'success': False, 'message': 'Only the receiver can accept or reject trades.'}), 403
        flash('Only the receiver can accept or reject trades.', 'danger')
        return redirect(url_for('main.my_trades'))
    
    # Sender can cancel pending or accepted trades, receiver can cancel accepted trades
    if action == 'cancel':
        if trade.status == 'pending' and trade.sender_id != current_user.id:
            if is_ajax:
                return jsonify({'success': False, 'message': 'Only the sender can cancel pending trades.'}), 403
            flash('Only the sender can cancel pending trades.', 'danger')
            return redirect(url_for('main.my_trades'))
        elif trade.status == 'accepted' and trade.sender_id != current_user.id and trade.receiver_id != current_user.id:
            if is_ajax:
                return jsonify({'success': False, 'message': 'You cannot cancel this trade.'}), 403
            flash('You cannot cancel this trade.', 'danger')
            return redirect(url_for('main.my_trades'))
    
    # Only pending or accepted trades can be cancelled
    if action == 'cancel' and trade.status not in ['pending', 'accepted']:
        if is_ajax:
            return jsonify({'success': False, 'message': 'This trade cannot be cancelled.'}), 400
        flash('This trade cannot be cancelled.', 'info')
        return redirect(url_for('main.my_trades'))
    
    # Only pending trades can be accepted or rejected
    if action in ['accept', 'reject'] and trade.status != 'pending':
        if is_ajax:
            return jsonify({'success': False, 'message': 'This trade is no longer pending.'}), 400
        flash('This trade is no longer pending.', 'info')
        return redirect(url_for('main.my_trades'))

    # Only accepted trades can be completed
    if action == 'complete' and trade.status != 'accepted':
        if is_ajax:
            return jsonify({'success': False, 'message': 'Only accepted trades can be marked as completed.'}), 400
        flash('Only accepted trades can be marked as completed.', 'info')
        return redirect(url_for('main.my_trades'))

    if action == 'accept':
        trade.status = 'accepted'
        trade.accepted_at = malaysia_now()
        # Create notification for sender
        notification = Notification(
            user_id=trade.sender_id,
            type='trade_accepted',
            content=f"Your trade proposal for {trade.requested_item.name} has been accepted!",
            trade_id=trade.id
        )
        db.session.add(notification)
        flash('Trade accepted!', 'success')
    elif action == 'reject':
        trade.status = 'rejected'
        # Create notification for sender
        notification = Notification(
            user_id=trade.sender_id,
            type='trade_rejected',
            content=f"Your trade proposal for {trade.requested_item.name} has been rejected.",
            trade_id=trade.id
        )
        db.session.add(notification)
        flash('Trade rejected.', 'info')
    elif action == 'cancel':
        trade.status = 'cancelled'
        # Create notification for the other party
        if current_user.id == trade.sender_id:
            # Sender cancelled, notify receiver
            notification = Notification(
                user_id=trade.receiver_id,
                type='trade_cancelled',
                content=f"A trade proposal for your item {trade.requested_item.name} has been cancelled.",
                trade_id=trade.id
            )
        else:
            # Receiver cancelled, notify sender
            notification = Notification(
                user_id=trade.sender_id,
                type='trade_cancelled',
                content=f"Your trade proposal for {trade.requested_item.name} has been cancelled by the item owner.",
                trade_id=trade.id
            )
        db.session.add(notification)
        flash('Trade cancelled.', 'info')
    elif action == 'complete':
        other_user_id = None
        if trade.sender_id == current_user.id:
            other_user_id = trade.receiver_id
            trade.sender_completed = True
            trade.sender_completed_at = malaysia_now()
            
            # Notify the other party that they need to confirm completion within 48 hours
            notification = Notification(
                user_id=other_user_id,
                type='trade_completion_reminder',
                content=f"{current_user.username} has marked the trade for {trade.requested_item.name} as completed. Please confirm completion within 48 hours.",
                trade_id=trade.id
            )
            db.session.add(notification)
            
            if trade.receiver_completed:
                trade.status = 'completed'
                trade.completed_at = malaysia_now()
                # Send rating reminder notifications
                _send_rating_reminder_notifications(trade)
                # Send completion notification to the other party
                completion_notification = Notification(
                    user_id=other_user_id,
                    type='trade_completed',
                    content=f"Trade for {trade.requested_item.name} has been completed by both parties!",
                    trade_id=trade.id
                )
                db.session.add(completion_notification)
        
        elif trade.receiver_id == current_user.id:
            other_user_id = trade.sender_id
            trade.receiver_completed = True
            trade.receiver_completed_at = malaysia_now()
            
            # Notify the other party that they need to confirm completion within 48 hours
            notification = Notification(
                user_id=other_user_id,
                type='trade_completion_reminder',
                content=f"{current_user.username} has marked the trade for {trade.requested_item.name} as completed. Please confirm completion within 48 hours.",
                trade_id=trade.id
            )
            db.session.add(notification)
            
            if trade.sender_completed:
                trade.status = 'completed'
                trade.completed_at = malaysia_now()
                # Send rating reminder notifications
                _send_rating_reminder_notifications(trade)
                # Send completion notification to the other party
                completion_notification = Notification(
                    user_id=other_user_id,
                    type='trade_completed',
                    content=f"Trade for {trade.requested_item.name} has been completed by both parties!",
                    trade_id=trade.id
                )
                db.session.add(completion_notification)
        
        flash('Trade marked as completed!', 'success')
    
    try:
        db.session.commit()
        
        # Handle AJAX requests
        if is_ajax:
            success_messages = {
                'accept': 'Trade accepted successfully!',
                'reject': 'Trade rejected successfully.',
                'cancel': 'Trade cancelled successfully.',
                'complete': 'Trade marked as completed!'
            }
            return jsonify({
                'success': True, 
                'message': success_messages.get(action, 'Action completed successfully!'),
                'new_status': trade.status
            })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error processing trade action: {str(e)}")
        
        # Handle AJAX error response
        if is_ajax:
            return jsonify({'success': False, 'message': 'An error occurred. Please try again.'}), 500
        
        flash('An error occurred. Please try again.', 'danger')
    
    return redirect(url_for('main.my_trades', status=trade.status))

def get_latest_message(user1_id, user2_id):
    """Get the latest message between two users."""
    return Message.query.filter(
        ((Message.sender_id == user1_id) & (Message.receiver_id == user2_id)) |
        ((Message.sender_id == user2_id) & (Message.receiver_id == user1_id))
    ).order_by(Message.created_at.desc()).first()

@main.route('/messages')
@main.route('/messages/<int:user_id>', methods=['GET', 'POST'])
@login_required
def messages(user_id=None):
    # First, get the latest message for each conversation using a subquery
    latest_messages_subquery = db.session.query(
        func.max(Message.id).label('max_id'),
        case(
            (Message.sender_id == current_user.id, Message.receiver_id),
            else_=Message.sender_id
        ).label('other_user_id')
    ).filter(
        (Message.sender_id == current_user.id) | (Message.receiver_id == current_user.id)
    ).group_by(
        case(
            (Message.sender_id == current_user.id, Message.receiver_id),
            else_=Message.sender_id
        )
    ).subquery()

    # Get unread count for each user
    unread_counts_subquery = db.session.query(
        Message.sender_id.label('sender_id'),
        func.count().label('unread_count')
    ).filter(
        Message.receiver_id == current_user.id,
        Message.is_read == False
    ).group_by(
        Message.sender_id
    ).subquery()

    # Get all users who have exchanged messages with current user
    message_partners = db.session.query(
        User,
        func.coalesce(unread_counts_subquery.c.unread_count, 0).label('unread_count'),
        case(
            (Message.content != None, Message.content),
            else_=None
        ).label('latest_message_content'),
        Message.created_at.label('latest_message_time'),
        Message.sender_id.label('latest_message_sender_id')
    ).join(
        latest_messages_subquery,
        User.id == latest_messages_subquery.c.other_user_id
    ).join(
        Message,
        Message.id == latest_messages_subquery.c.max_id
    ).outerjoin(
        unread_counts_subquery,
        User.id == unread_counts_subquery.c.sender_id
    ).filter(
        User.id != current_user.id
    ).group_by(
        User.id,
        unread_counts_subquery.c.unread_count,
        Message.content,
        Message.created_at,
        Message.sender_id
    ).order_by(Message.created_at.desc()).all()

    other_user = User.query.get(user_id) if user_id else None
    messages = []
    
    if other_user:
        # Mark messages as read first
        Message.query.filter_by(
            receiver_id=current_user.id,
            sender_id=user_id,
            is_read=False
        ).update({Message.is_read: True})
        db.session.commit()
        
        if request.method == 'POST':
            content = request.form.get('content', '').strip()  # Strip whitespace
            photos = request.files.getlist('photos')
            
            # Create message if there's content or photos
            has_photos = photos and any(photo.filename for photo in photos)
            
            if content or has_photos:  # Allow sending if either content or photos exist
                message = Message(
                    sender_id=current_user.id,
                    receiver_id=user_id,
                    content=content if content else None,
                    is_read=False
                )
                db.session.add(message)
                db.session.flush()  # This assigns an ID to the message
                
                # Handle multiple photo uploads
                if has_photos:
                    # Create message_images directory if it doesn't exist
                    message_images_path = os.path.join(current_app.root_path, 'static', 'uploads', 'message_images')
                    os.makedirs(message_images_path, exist_ok=True)
                    
                    for photo in photos:
                        if photo.filename and allowed_file(photo.filename):
                            image_filename = secure_filename(photo.filename)
                            timestamp = int(malaysia_now().timestamp())
                            unique_filename = f"message_{message.id}_{timestamp}_{image_filename}"
                            photo.save(os.path.join(message_images_path, unique_filename))
                            
                            message_image = MessageImage(
                                message_id=message.id,
                                image_path=unique_filename
                            )
                            db.session.add(message_image)
                
                db.session.commit()
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'success': True})
                return redirect(url_for('main.messages', user_id=user_id))
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'error': 'Please provide a message or photos'})
            flash('Please provide a message or photos', 'danger')
            return redirect(url_for('main.messages', user_id=user_id))
        
        messages = Message.query.filter(
            ((Message.sender_id == current_user.id) & (Message.receiver_id == user_id)) |
            ((Message.sender_id == user_id) & (Message.receiver_id == current_user.id))
        ).order_by(Message.created_at.asc()).all()
    
    # Add datetime objects for date dividers
    now = malaysia_now()
    
    return render_template('main/messages.html', 
                         messages=messages, 
                         other_user=other_user,
                         message_partners=message_partners,
                         now=now,
                         timedelta=timedelta,
                         get_latest_message=get_latest_message)

@main.route('/messages/<int:user_id>/status')
@login_required
def check_message_status(user_id):
    # Get the latest message sent by current user to the other user
    latest_message = Message.query.filter_by(
        sender_id=current_user.id,
        receiver_id=user_id
    ).order_by(Message.created_at.desc()).first()
    
    if latest_message:
        return jsonify({'is_read': latest_message.is_read})
    return jsonify({'is_read': False})

@main.route('/review/<int:trade_id>', methods=['POST'])
@login_required
def review(trade_id):
    trade = Trade.query.get_or_404(trade_id)
    
    # Check if trade can be reviewed
    if trade.status != 'completed' or (trade.sender_id != current_user.id and trade.receiver_id != current_user.id):
        flash('You cannot review this trade.', 'danger')
        return redirect(url_for('main.my_trades'))
    
    # Check if the review is within the 30-day deadline
    if trade.completed_at:
        time_since_completion = malaysia_now() - trade.completed_at
        if time_since_completion.days > 30:
            flash('Review period has expired. You can only review trades within 30 days of completion.', 'warning')
            return redirect(url_for('main.my_trades'))
    
    # Check if user has already reviewed this trade
    existing_review = Review.query.filter_by(trade_id=trade_id, reviewer_id=current_user.id).first()
    if existing_review:
        flash('You have already reviewed this trade.', 'warning')
        return redirect(url_for('main.my_trades'))
    
    rating = request.form.get('rating', type=int)
    comment = request.form.get('comment')
    
    if not rating or not comment:
        flash('Both rating and comment are required.', 'danger')
        return redirect(url_for('main.my_trades'))
    
    review = Review(
        reviewer_id=current_user.id,
        reviewed_id=trade.receiver_id if current_user.id == trade.sender_id else trade.sender_id,
        trade_id=trade.id,
        rating=rating,
        comment=comment
    )
    db.session.add(review)
    db.session.commit()  # Commit to get review.id
    
    # Handle photo uploads
    photos = request.files.getlist('photos')
    if photos:
        review_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'reviews', str(review.id))
        os.makedirs(review_dir, exist_ok=True)
        
        for photo in photos:
            if photo and allowed_file(photo.filename):
                filename = secure_filename(photo.filename)
                photo.save(os.path.join(review_dir, filename))
                
                review_photo = ReviewPhoto(
                    review_id=review.id,
                    photo_path=filename
                )
                db.session.add(review_photo)
    
    db.session.commit()
    
    flash('Your review has been submitted!', 'success')
    return redirect(url_for('main.my_trades'))

@main.route('/favorites')
@login_required
def favorites():
    # Exclude items that are in accepted or completed trades
    subquery_requested = db.session.query(Trade.requested_item_id).filter(Trade.status.in_(['completed', 'accepted']))
    subquery_offered = db.session.query(TradeItem.item_id).join(Trade).filter(Trade.status.in_(['completed', 'accepted']))
    
    favorites = Favorite.query.filter_by(user_id=current_user.id).join(Item).filter(
        Item.is_active == True,
        ~Item.id.in_(subquery_requested),
        ~Item.id.in_(subquery_offered)
    ).all()
    return render_template('main/favorites.html', favorites=favorites)

@main.route('/favorite/<int:item_id>', methods=['POST'])
@login_required
def favorite_toggle(item_id):
    print(f"Favorite toggle called for item {item_id} by user {current_user.id}")
    item = Item.query.get_or_404(item_id)
    favorite = Favorite.query.filter_by(user_id=current_user.id, item_id=item_id).first()
    
    if favorite:
        print(f"Removing favorite for item {item_id}")
        db.session.delete(favorite)
        db.session.commit()
        print("Favorite removed successfully")
        return jsonify({'status': 'removed'})
    else:
        print(f"Adding favorite for item {item_id}")
        favorite = Favorite(user_id=current_user.id, item_id=item_id)
        db.session.add(favorite)
        db.session.commit()
        print("Favorite added successfully")
        return jsonify({'status': 'added'})

@main.route('/get_unread_count')
@login_required
def get_unread_count():
    count = Message.query.filter_by(
        receiver_id=current_user.id,
        is_read=False
    ).count()
    print(f"Unread messages count: {count}")  # Debug print
    return jsonify({'count': count})

@main.route('/search')
def search():
    query = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    category_id = request.args.get('category', type=int)
    condition = request.args.get('condition')
    state = request.args.get('state')
    city = request.args.get('city')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    sort_by = request.args.get('sort', 'newest')
    
    # Base query - exclude traded and accepted items
    subquery_requested = db.session.query(Trade.requested_item_id).filter(Trade.status.in_(['completed', 'accepted'])).subquery()
    subquery_offered = db.session.query(TradeItem.item_id).join(Trade).filter(Trade.status.in_(['completed', 'accepted'])).subquery()
    
    search_query = Item.query.filter_by(is_active=True).filter(
        ~Item.id.in_(subquery_requested),
        ~Item.id.in_(subquery_offered)
    )
    
    # Apply search filter
    if query:
        search_query = search_query.filter(
            or_(
                Item.name.ilike(f'%{query}%'),
                Item.description.ilike(f'%{query}%')
            )
        )
    
    # Apply category filter
    if category_id:
        search_query = search_query.filter_by(category_id=category_id)
    
    # Apply condition filter
    if condition:
        search_query = search_query.filter_by(condition=condition)
    
    # Apply state and city filters
    if state:
        search_query = search_query.join(User).filter(User.region == state)
        if city:
            search_query = search_query.filter(User.city == city)
    
    # Apply price range filter
    if min_price is not None:
        search_query = search_query.filter(Item.estimated_value >= min_price)
    if max_price is not None:
        search_query = search_query.filter(Item.estimated_value <= max_price)
    
    # Apply sorting
    if sort_by == 'oldest':
        search_query = search_query.order_by(Item.created_at.asc())
    elif sort_by == 'price_low':
        # Handle NULL values by putting them at the end
        search_query = search_query.order_by(case((Item.estimated_value.is_(None), 1), else_=0), Item.estimated_value.asc())
    elif sort_by == 'price_high':
        # Handle NULL values by putting them at the end
        search_query = search_query.order_by(case((Item.estimated_value.is_(None), 1), else_=0), Item.estimated_value.desc())
    else:  # newest (default)
        search_query = search_query.order_by(Item.created_at.desc())
    
    # Get paginated results
    items = search_query.paginate(page=page, per_page=12, error_out=False)
    
    # Get all categories
    categories = Category.query.all()
    
    # Get states
    states = [state for state, _ in MALAYSIA_STATES if state]
    
    # Get cities for the selected state from predefined list
    cities = []
    if state and state in MALAYSIA_CITIES:
        cities = MALAYSIA_CITIES[state]
    
    return render_template('main/search.html', 
                         query=query,
                         items=items, 
                         categories=categories,
                         states=states,
                         cities=cities,
                         current_state=state,
                         current_city=city,
                         current_category=category_id,
                         current_condition=condition,
                         MALAYSIA_CITIES=MALAYSIA_CITIES)

@main.route('/item/<int:item_id>/flag', methods=['GET', 'POST'])
@login_required
def flag_item(item_id):
    item = Item.query.get_or_404(item_id)
    if item.user_id == current_user.id:
        flash('You cannot report your own item.', 'danger')
        return redirect(url_for('main.item', item_id=item.id))
    
    # Check if user has already flagged this item
    existing_flag = Flag.query.filter_by(
        item_id=item.id,
        user_id=current_user.id,
        status='pending'
    ).first()
    
    if existing_flag:
        flash('You have already reported this item.', 'info')
        return redirect(url_for('main.item', item_id=item.id))
    
    form = FlagForm()
    if form.validate_on_submit():
        flag = Flag(
            item_id=item.id,
            user_id=current_user.id,
            violation_type=form.violation_type.data,
            reason=form.reason.data,
            status='pending'
        )
        db.session.add(flag)
        
        # Create notification for flagged item
        violation_display = dict(form.violation_type.choices)[form.violation_type.data]
        notification = Notification(
            user_id=item.user_id,
            type='flag',
            content=f"Your item '{item.name}' has been reported for: {violation_display}",
            item_id=item.id
        )
        db.session.add(notification)
        
        db.session.commit()
        flash('Thank you for reporting this item. Our moderators will review it shortly.', 'success')
        return redirect(url_for('main.item', item_id=item.id))
    
    return render_template('main/flag_item.html', title='Report Item', form=form, item=item) 

@main.route('/get_notification_count')
@login_required
def get_notification_count():
    count = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).count()
    return jsonify({'count': count})

@main.route('/notifications')
@login_required
def notifications():
    # Check for auto-completion
    _check_auto_completion()
    
    notifications = Notification.query.filter_by(
        user_id=current_user.id
    ).order_by(Notification.created_at.desc()).all()
    
    # Mark all notifications as read
    Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).update({Notification.is_read: True})
    db.session.commit()
    
    return render_template('main/notifications.html', notifications=notifications)

@main.route('/my-trades')
@main.route('/my-trades/<string:status>')
@login_required
def my_trades(status=None):
    # Check for auto-completion on every visit
    _check_auto_completion()

    # Get all pending trades for the counter - exclude traded items
    # Subqueries to find items that are already traded
    traded_requested_items = db.session.query(Trade.requested_item_id).filter(Trade.status == 'completed')
    traded_offered_items = db.session.query(TradeItem.item_id).join(Trade).filter(Trade.status == 'completed')
    
    pending_trades = (
        Trade.query
        .filter(or_(Trade.sender_id == current_user.id, Trade.receiver_id == current_user.id))
        .filter(Trade.status == 'pending')
        .filter(~Trade.requested_item_id.in_(traded_requested_items))  # Exclude traded requested items
        .filter(~Trade.id.in_(  # Exclude trades with traded offered items
            db.session.query(Trade.id)
            .join(TradeItem)
            .filter(TradeItem.item_id.in_(traded_offered_items))
        ))
        .options(
            joinedload(Trade.sender),
            joinedload(Trade.receiver),
            joinedload(Trade.requested_item),
            joinedload(Trade.offered_items).joinedload(TradeItem.item)
        )
        .order_by(Trade.updated_at.desc())
        .all()
    )

    # Get trades for the current status (with traded items filtering)
    trades_query = (
        Trade.query
        .filter(or_(Trade.sender_id == current_user.id, Trade.receiver_id == current_user.id))
        .filter(~Trade.requested_item_id.in_(traded_requested_items))  # Exclude traded requested items
        .filter(~Trade.id.in_(  # Exclude trades with traded offered items
            db.session.query(Trade.id)
            .join(TradeItem)
            .filter(TradeItem.item_id.in_(traded_offered_items))
        ))
        .options(
            joinedload(Trade.sender),
            joinedload(Trade.receiver),
            joinedload(Trade.requested_item),
            joinedload(Trade.offered_items).joinedload(TradeItem.item)
        )
    )

    # Filter by status if provided
    if status:
        if status == 'pending_approval':
            current_trades = pending_trades
        elif status == 'completed':
            # Show trades in completed tab if:
            # 1. Trade status is 'completed' OR
            # 2. Current user has marked their side as completed
            # Note: Don't filter traded items for completed trades since they are completed
            completed_query = (
                Trade.query
                .filter(or_(Trade.sender_id == current_user.id, Trade.receiver_id == current_user.id))
                .options(
                    joinedload(Trade.sender),
                    joinedload(Trade.receiver),
                    joinedload(Trade.requested_item),
                    joinedload(Trade.offered_items).joinedload(TradeItem.item)
                )
            )
            current_trades = completed_query.filter(
                or_(
                    Trade.status == 'completed',
                    and_(
                        Trade.status == 'accepted',
                        or_(
                            and_(Trade.sender_id == current_user.id, Trade.sender_completed == True),
                            and_(Trade.receiver_id == current_user.id, Trade.receiver_completed == True)
                        )
                    )
                )
            ).order_by(Trade.updated_at.desc()).all()
        elif status == 'accepted':
            # Only show in accepted tab if user hasn't marked their side as completed
            # Also exclude traded items
            current_trades = trades_query.filter(
                and_(
                    Trade.status == 'accepted',
                    or_(
                        and_(Trade.sender_id == current_user.id, Trade.sender_completed == False),
                        and_(Trade.receiver_id == current_user.id, Trade.receiver_completed == False)
                    )
                )
            ).filter(~Trade.requested_item_id.in_(traded_requested_items)
            ).filter(~Trade.id.in_(
                db.session.query(Trade.id)
                .join(TradeItem)
                .filter(TradeItem.item_id.in_(traded_offered_items))
            )).order_by(Trade.updated_at.desc()).all()
        elif status in ['rejected', 'cancelled']:
            # For rejected and cancelled trades, also exclude traded items
            current_trades = trades_query.filter(Trade.status == status
            ).filter(~Trade.requested_item_id.in_(traded_requested_items)
            ).filter(~Trade.id.in_(
                db.session.query(Trade.id)
                .join(TradeItem)
                .filter(TradeItem.item_id.in_(traded_offered_items))
            )).order_by(Trade.updated_at.desc()).all()
        else:
            current_trades = trades_query.filter(Trade.status == status).order_by(Trade.updated_at.desc()).all()
    else:
        current_trades = pending_trades

    return render_template('main/my_trades.html', 
                         pending_trades=pending_trades,
                         current_trades=current_trades,
                         current_status=status)

@main.route("/delete_item_photo/<int:item_id>/<int:photo_id>")
@login_required
def delete_item_photo(item_id, photo_id):
    item = Item.query.get_or_404(item_id)
    if item.user_id != current_user.id:
        abort(403)
    
    photo = ItemPhoto.query.get_or_404(photo_id)
    if photo.item_id != item_id:
        abort(403)
    
    # Remove the photo from the database
    db.session.delete(photo)
    db.session.commit()
    
    return jsonify(success=True)

@main.route('/get_cities/<state>')
def get_cities(state):
    if state in MALAYSIA_CITIES:
        cities = MALAYSIA_CITIES[state]
        return jsonify({'cities': cities})
    return jsonify({'cities': []})

@main.route('/delete_photo/<int:photo_id>', methods=['POST'])
@login_required
def delete_photo(photo_id):
    photo = ItemPhoto.query.get_or_404(photo_id)
    item = Item.query.get(photo.item_id)
    
    if item.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    try:
        # Delete the physical file
        file_path = os.path.join(current_app.root_path, 'static', 'uploads', 'items', str(item.id), photo.photo_path)
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Delete from database
        db.session.delete(photo)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting photo: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to delete photo'}), 500

@main.route('/check-duplicate-trade/<int:item_id>')
@login_required
def check_duplicate_trade(item_id):
    """Check if user already has a pending trade for this item"""
    item = Item.query.get_or_404(item_id)
    
    # Check for existing pending trade for the same item
    existing_trade = Trade.query.filter_by(
        sender_id=current_user.id,
        receiver_id=item.user_id,
        requested_item_id=item.id,
        status='pending'
    ).first()
    
    return jsonify({'hasDuplicate': existing_trade is not None})

@main.route('/debug-auto-completion')
@login_required
def debug_auto_completion():
    """Debug route to check auto-completion status"""
    now = malaysia_now()
    auto_complete_minutes = 2
    
    # Find all accepted trades for current user
    accepted_trades = Trade.query.filter(
        Trade.status == 'accepted',
        or_(Trade.sender_id == current_user.id, Trade.receiver_id == current_user.id)
    ).all()
    
    # Also test the actual query used in auto-completion
    query_trades = Trade.query.filter(
        Trade.status == 'accepted',
        # Ensure that both users haven't already completed (avoid double completion)
        ~(Trade.sender_completed == True and Trade.receiver_completed == True),
        or_(
            and_(
                Trade.sender_completed == True,
                Trade.receiver_completed == False,
                Trade.sender_completed_at.isnot(None),
                now - Trade.sender_completed_at >= timedelta(minutes=auto_complete_minutes)
            ),
            and_(
                Trade.receiver_completed == True,
                Trade.sender_completed == False,
                Trade.receiver_completed_at.isnot(None),
                now - Trade.receiver_completed_at >= timedelta(minutes=auto_complete_minutes)
            )
        )
    ).all()
    
    debug_info = []
    for trade in accepted_trades:
        info = {
            'trade_id': trade.id,
            'sender_completed': trade.sender_completed,
            'receiver_completed': trade.receiver_completed,
            'sender_completed_at': trade.sender_completed_at.isoformat() if trade.sender_completed_at else None,
            'receiver_completed_at': trade.receiver_completed_at.isoformat() if trade.receiver_completed_at else None,
            'both_completed': trade.sender_completed and trade.receiver_completed,
            'found_in_query': trade.id in [t.id for t in query_trades]
        }
        
        if trade.sender_completed and trade.sender_completed_at:
            time_diff = (now - trade.sender_completed_at).total_seconds() / 60
            info['sender_minutes_ago'] = round(time_diff, 2)
            info['sender_eligible_for_auto'] = time_diff >= auto_complete_minutes and not trade.receiver_completed
            
        if trade.receiver_completed and trade.receiver_completed_at:
            time_diff = (now - trade.receiver_completed_at).total_seconds() / 60
            info['receiver_minutes_ago'] = round(time_diff, 2)
            info['receiver_eligible_for_auto'] = time_diff >= auto_complete_minutes and not trade.sender_completed
            
        debug_info.append(info)
    
    return jsonify({
        'current_time': now.isoformat(),
        'auto_complete_minutes': auto_complete_minutes,
        'accepted_trades': debug_info,
        'query_found_trades': len(query_trades),
        'query_trade_ids': [t.id for t in query_trades]
    })

@main.route('/trigger-auto-completion')
@login_required
def trigger_auto_completion():
    """Manually trigger auto-completion for testing"""
    _check_auto_completion()
    return jsonify({'message': 'Auto-completion check triggered. Check logs for details.'})

@main.route('/force-auto-complete/<int:trade_id>')
@login_required
def force_auto_complete(trade_id):
    """Force auto-complete a specific trade for testing"""
    trade = Trade.query.get_or_404(trade_id)
    
    # Check if user is involved in this trade
    if trade.sender_id != current_user.id and trade.receiver_id != current_user.id:
        return jsonify({'error': 'You are not involved in this trade'}), 403
        
    if trade.status != 'accepted':
        return jsonify({'error': 'Trade is not in accepted status'}), 400
    
    now = malaysia_now()
    
    # Force auto-complete based on who completed first
    if trade.sender_completed and not trade.receiver_completed:
        trade.status = 'completed'
        trade.completed_at = now
        trade.auto_completed = True
        trade.receiver_completed = True
        trade.receiver_completed_at = now
        
        notification = Notification(
            user_id=trade.receiver_id,
            type='trade_auto_completed',
            content=f"The trade for {trade.requested_item.name} has been automatically marked as completed after 2 minutes.",
            trade_id=trade.id
        )
        db.session.add(notification)
        _send_rating_reminder_notifications(trade)
        
    elif trade.receiver_completed and not trade.sender_completed:
        trade.status = 'completed'
        trade.completed_at = now
        trade.auto_completed = True
        trade.sender_completed = True
        trade.sender_completed_at = now
        
        notification = Notification(
            user_id=trade.sender_id,
            type='trade_auto_completed',
            content=f"The trade for {trade.requested_item.name} has been automatically marked as completed after 2 minutes.",
            trade_id=trade.id
        )
        db.session.add(notification)
        _send_rating_reminder_notifications(trade)
        
    else:
        return jsonify({'error': 'Trade does not meet auto-completion criteria'}), 400
    
    db.session.commit()
    return jsonify({'message': f'Trade {trade_id} has been force auto-completed'})

@main.route('/cron/auto-completion')
def cron_auto_completion():
    """Background cron job endpoint for auto-completion - no login required"""
    # Optional: Add a secret key for security
    secret = request.args.get('secret')
    expected_secret = current_app.config.get('CRON_SECRET', 'your-secret-key-here')
    
    if secret != expected_secret:
        return jsonify({'error': 'Unauthorized'}), 401
    
    _check_auto_completion()
    return jsonify({'message': 'Auto-completion check completed successfully'})

def start_background_scheduler():
    """Start background scheduler for auto-completion checks"""
    def run_scheduler():
        while True:
            try:
                time.sleep(60)  # Check every minute
                with current_app.app_context():
                    _check_auto_completion()
            except Exception as e:
                print(f"Background scheduler error: {str(e)}")
    
    # Start the scheduler in a daemon thread
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    print("Background auto-completion scheduler started")

@main.route('/start-scheduler')
@login_required  
def start_scheduler_route():
    """Start the background scheduler (admin only)"""
    if not current_user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403
    
    start_background_scheduler()
    return jsonify({'message': 'Background scheduler started'})