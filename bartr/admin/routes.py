from flask import render_template, flash, redirect, url_for, request, jsonify
from flask_login import login_required, current_user
from bartr import db
from bartr.models import User, Item, Category, Trade, TradeItem, Flag, malaysia_now
from bartr.admin import admin
from bartr.admin.forms import CategoryForm
from functools import wraps
import os
import datetime
from flask import send_file, current_app

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@admin.route('/dashboard')
@login_required
@admin_required
def dashboard():
    total_users = User.query.count()
    total_items = Item.query.count()
    active_trades = Trade.query.filter_by(status='pending').count()
    flagged_items = Item.query.filter_by(is_flagged=True).count()
    
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_items = Item.query.order_by(Item.created_at.desc()).limit(5).all()
    pending_flags = Flag.query.filter_by(status='pending').order_by(Flag.created_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         total_items=total_items,
                         active_trades=active_trades,
                         flagged_items=flagged_items,
                         recent_users=recent_users,
                         recent_items=recent_items,
                         pending_flags=pending_flags)

@admin.route('/users')
@login_required
@admin_required
def users():
    page = request.args.get('page', 1, type=int)
    filter_type = request.args.get('filter', 'all')
    search = request.args.get('search', '')
    
    query = User.query
    
    # Apply search filter
    if search:
        query = query.filter(
            (User.username.ilike(f'%{search}%')) |
            (User.email.ilike(f'%{search}%')) |
            (User.name.ilike(f'%{search}%'))
        )
    
    # Apply status filter
    if filter_type == 'active':
        query = query.filter(User.is_active == True)
    elif filter_type == 'suspended':
        query = query.filter(User.is_active == False)
    elif filter_type == 'new':
        from datetime import datetime, timedelta
        seven_days_ago = malaysia_now() - timedelta(days=7)
        query = query.filter(User.created_at >= seven_days_ago)
    
    users = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False)
    
    total_users = User.query.count()
    active_users = User.query.filter(User.is_active == True).count()
    suspended_users = User.query.filter(User.is_active == False).count()
    
    return render_template('admin/users.html', 
                         users=users, 
                         filter_type=filter_type, 
                         search=search,
                         total_users=total_users,
                         active_users=active_users,
                         suspended_users=suspended_users)

@admin.route('/user/<int:user_id>/toggle-status')
@login_required
@admin_required
def toggle_user_status(user_id):
    user = User.query.get_or_404(user_id)
    if user == current_user:
        flash('You cannot deactivate your own account.', 'danger')
    else:
        user.is_active = not user.is_active
        db.session.commit()
        status = 'activated' if user.is_active else 'suspended'
        flash(f'User {user.username} has been {status}.', 'success')
    return redirect(url_for('admin.users'))

@admin.route('/user/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user == current_user:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('admin.users'))
    
    try:
        # Delete user's related data first
        from bartr.models import Item, Trade, Review, Message, Favorite, Flag, Notification
        
        # Delete user's items and their related data
        for item in user.items:
            # Delete item photos
            for photo in item.photos:
                db.session.delete(photo)
            # Delete item favorites
            for favorite in item.favorites:
                db.session.delete(favorite)
            # Delete item flags
            for flag in item.flags:
                db.session.delete(flag)
            db.session.delete(item)
        
        # Delete user's trades
        for trade in user.sent_trades + user.received_trades:
            # Delete trade items
            for trade_item in trade.offered_items:
                db.session.delete(trade_item)
            db.session.delete(trade)
        
        # Delete user's reviews
        for review in user.reviews_given + user.reviews_received:
            # Delete review photos
            for photo in review.photos:
                db.session.delete(photo)
            db.session.delete(review)
        
        # Delete user's messages
        messages_sent = Message.query.filter_by(sender_id=user.id).all()
        messages_received = Message.query.filter_by(receiver_id=user.id).all()
        for message in messages_sent + messages_received:
            # Delete message images
            for image in message.images:
                db.session.delete(image)
            db.session.delete(message)
        
        # Delete user's favorites
        for favorite in user.favorites:
            db.session.delete(favorite)
            
        # Delete user's flags
        for flag in user.flags:
            db.session.delete(flag)
            
        # Delete user's notifications
        notifications = Notification.query.filter_by(user_id=user.id).all()
        for notification in notifications:
            db.session.delete(notification)
        
        # Finally delete the user
        username = user.username
        db.session.delete(user)
        db.session.commit()
        
        flash(f'User {username} and all associated data have been permanently deleted.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting user: {str(e)}', 'danger')
    
    return redirect(url_for('admin.users'))

@admin.route('/categories', methods=['GET', 'POST'])
@login_required
@admin_required
def categories():
    form = CategoryForm()
    if form.validate_on_submit():
        # Get the next order value
        max_order = db.session.query(db.func.max(Category.order)).scalar() or 0
        category = Category(name=form.name.data, description=form.description.data, order=max_order + 1)
        db.session.add(category)
        db.session.commit()
        flash('New category has been created!', 'success')
        return redirect(url_for('admin.categories'))
    
    # Initialize order values for categories that don't have them
    categories_without_order = Category.query.filter(
        (Category.order == 0) | (Category.order.is_(None))
    ).order_by(Category.id).all()
    if categories_without_order:
        for i, category in enumerate(categories_without_order):
            category.order = i + 1
        db.session.commit()
    
    categories = Category.query.order_by(Category.order, Category.id).all()
    return render_template('admin/categories.html', form=form, categories=categories)

@admin.route('/category/<int:category_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_category(category_id):
    category = Category.query.get_or_404(category_id)
    form = CategoryForm(obj=category)
    
    if form.validate_on_submit():
        category.name = form.name.data
        category.description = form.description.data
        db.session.commit()
        flash('Category has been updated!', 'success')
        return redirect(url_for('admin.categories'))
    
    categories = Category.query.order_by(Category.order, Category.id).all()
    return render_template('admin/categories.html', form=form, categories=categories, edit_category=category)

@admin.route('/category/<int:category_id>/move-up')
@login_required
@admin_required
def move_category_up(category_id):
    category = Category.query.get_or_404(category_id)
    categories = Category.query.order_by(Category.order, Category.id).all()
    
    current_index = next((i for i, cat in enumerate(categories) if cat.id == category_id), None)
    if current_index is not None and current_index > 0:
        # Swap order with previous category
        prev_category = categories[current_index - 1]
        category_order = category.order
        prev_order = prev_category.order
        
        category.order = prev_order
        prev_category.order = category_order
        db.session.commit()
        
        flash('Category moved up.', 'success')
    
    return redirect(url_for('admin.categories'))

@admin.route('/category/<int:category_id>/move-down')
@login_required
@admin_required
def move_category_down(category_id):
    category = Category.query.get_or_404(category_id)
    categories = Category.query.order_by(Category.order, Category.id).all()
    
    current_index = next((i for i, cat in enumerate(categories) if cat.id == category_id), None)
    if current_index is not None and current_index < len(categories) - 1:
        # Swap order with next category
        next_category = categories[current_index + 1]
        category_order = category.order
        next_order = next_category.order
        
        category.order = next_order
        next_category.order = category_order
        db.session.commit()
        
        flash('Category moved down.', 'success')
    
    return redirect(url_for('admin.categories'))

@admin.route('/categories/reorder', methods=['POST'])
@login_required
@admin_required
def reorder_categories():
    try:
        category_ids = request.json.get('category_ids', [])
        
        # Update the order field for each category
        for new_position, category_id in enumerate(category_ids):
            category = Category.query.get(int(category_id))
            if category:
                category.order = new_position
        
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@admin.route('/category/<int:category_id>/delete')
@login_required
@admin_required
def delete_category(category_id):
    category = Category.query.get_or_404(category_id)
    if Item.query.filter_by(category_id=category_id).first():
        flash('Cannot delete category that has items.', 'danger')
    else:
        db.session.delete(category)
        db.session.commit()
        flash('Category has been deleted.', 'success')
    return redirect(url_for('admin.categories'))

@admin.route('/flags')
@login_required
@admin_required
def flags():
    page = request.args.get('page', 1, type=int)
    flags = Flag.query.order_by(Flag.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False)
    return render_template('admin/flags.html', flags=flags)

@admin.route('/flag/<int:flag_id>/resolve')
@login_required
@admin_required
def resolve_flag(flag_id):
    flag = Flag.query.get_or_404(flag_id)
    flag.status = 'resolved'
    flag.item.is_flagged = True
    db.session.commit()
    flash('Flag has been resolved and item has been marked.', 'success')
    return redirect(url_for('admin.flags'))

@admin.route('/item/<int:item_id>/remove', methods=['POST'])
@login_required
@admin_required
def remove_item(item_id):
    item = Item.query.get_or_404(item_id)
    
    try:
        # Delete item's related data first
        from bartr.models import ItemPhoto, Favorite, Flag, Notification, TradeItem
        
        # Delete item photos
        for photo in item.photos:
            db.session.delete(photo)
        
        # Delete item favorites
        for favorite in item.favorites:
            db.session.delete(favorite)
        
        # Delete item flags
        for flag in item.flags:
            db.session.delete(flag)
            
        # Delete notifications related to this item
        notifications = Notification.query.filter_by(item_id=item.id).all()
        for notification in notifications:
            db.session.delete(notification)
        
        # Delete trade items that reference this item
        trade_items = TradeItem.query.filter_by(item_id=item.id).all()
        for trade_item in trade_items:
            db.session.delete(trade_item)
        
        # Finally delete the item
        item_name = item.name
        db.session.delete(item)
        db.session.commit()
        
        flash(f'Item "{item_name}" has been permanently removed.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error removing item: {str(e)}', 'danger')
    
    return redirect(request.referrer or url_for('admin.flags'))

@admin.route('/flag/<int:flag_id>/dismiss')
@login_required
@admin_required
def dismiss_flag(flag_id):
    flag = Flag.query.get_or_404(flag_id)
    flag.status = 'dismissed'
    db.session.commit()
    flash('Flag has been dismissed.', 'success')
    return redirect(url_for('admin.flags'))

@admin.route('/trades')
@login_required
@admin_required
def trades():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'all')
    
    query = Trade.query
    
    # Apply status filter
    if status_filter != 'all':
        query = query.filter(Trade.status == status_filter)
    
    # Eagerly load the offered items and related data
    trades = query.options(
        db.joinedload(Trade.offered_items).joinedload(TradeItem.item),
        db.joinedload(Trade.requested_item),
        db.joinedload(Trade.sender),
        db.joinedload(Trade.receiver)
    ).order_by(Trade.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False)
    
    # Get trade statistics
    total_trades = Trade.query.count()
    pending_trades = Trade.query.filter(Trade.status == 'pending').count()
    completed_trades = Trade.query.filter(Trade.status == 'completed').count()
    cancelled_trades = Trade.query.filter(Trade.status == 'cancelled').count()
    
    return render_template('admin/trades.html', 
                         trades=trades, 
                         status_filter=status_filter,
                         total_trades=total_trades,
                         pending_trades=pending_trades,
                         completed_trades=completed_trades,
                         cancelled_trades=cancelled_trades)


@admin.route('/items')
@login_required
@admin_required
def items():
    page = request.args.get('page', 1, type=int)
    filter_type = request.args.get('filter', 'all')
    search = request.args.get('search', '')
    category_id = request.args.get('category', type=int)
    
    query = Item.query
    
    # Apply search filter
    if search:
        query = query.filter(
            (Item.name.ilike(f'%{search}%')) |
            (Item.description.ilike(f'%{search}%'))
        )
    
    # Apply category filter
    if category_id:
        query = query.filter(Item.category_id == category_id)
    
    # Apply status filter
    if filter_type == 'active':
        query = query.filter(Item.is_active == True)
    elif filter_type == 'inactive':
        query = query.filter(Item.is_active == False)
    elif filter_type == 'flagged':
        query = query.filter(Item.is_flagged == True)
    
    items = query.order_by(Item.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False)
    
    # Get item statistics
    total_items = Item.query.count()
    active_items = Item.query.filter(Item.is_active == True).count()
    flagged_items = Item.query.filter(Item.is_flagged == True).count()
    
    # Get categories for filter
    categories = Category.query.all()
    
    return render_template('admin/items.html', 
                         items=items, 
                         filter_type=filter_type, 
                         search=search,
                         category_id=category_id,
                         total_items=total_items,
                         active_items=active_items,
                         flagged_items=flagged_items,
                         categories=categories)

@admin.route('/item/<int:item_id>/toggle-status')
@login_required
@admin_required
def toggle_item_status(item_id):
    item = Item.query.get_or_404(item_id)
    was_active = item.is_active
    item.is_active = not item.is_active
    
    # Send notification if item is being deactivated
    if was_active and not item.is_active:
        from bartr.models import Notification
        notification = Notification(
            user_id=item.user_id,
            type='item_deactivated',
            content=f'Your item "{item.name}" has been deactivated by an administrator.',
            item_id=item.id
        )
        db.session.add(notification)
    
    db.session.commit()
    status = 'activated' if item.is_active else 'deactivated'
    flash(f'Item "{item.name}" has been {status}.', 'success')
    return redirect(url_for('admin.items'))

@admin.route('/backups')
@login_required
@admin_required
def backups():
    import os
    from datetime import datetime
    backup_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backups')
    files = []
    for filename in os.listdir(backup_dir):
        filepath = os.path.join(backup_dir, filename)
        if os.path.isfile(filepath):
            stat = os.stat(filepath)
            files.append({
                'filename': filename,
                'created_at': datetime.fromtimestamp(stat.st_mtime),
                'size': stat.st_size
            })
    # Sort by created_at descending
    files.sort(key=lambda x: x['created_at'], reverse=True)
    return render_template('admin/backups.html', backups=files)

@admin.route('/backups/create', methods=['POST'])
@login_required
@admin_required
def create_backup():
    backup_dir = os.path.join(current_app.root_path, 'backups')
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    db_uri = current_app.config['SQLALCHEMY_DATABASE_URI']
    
    backup_filename = f'backup_{timestamp}.sql'
    backup_path = os.path.join(backup_dir, backup_filename)
    
    try:
        from sqlalchemy import create_engine, inspect, text
        
        # Create database engine
        engine = create_engine(db_uri)
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        with open(backup_path, 'w', encoding='utf-8') as f:
            # Write header
            f.write(f"-- Database backup created on {datetime.datetime.now()}\n")
            f.write(f"-- Backup file: {backup_filename}\n\n")
            
            # Disable foreign key checks
            f.write("SET FOREIGN_KEY_CHECKS = 0;\n\n")
            
            with engine.connect() as conn:
                # Export each table
                for table in tables:
                    f.write(f"-- Table: {table}\n")
                    
                    # Get table structure
                    if db_uri.startswith('mysql'):
                        result = conn.execute(text(f"SHOW CREATE TABLE `{table}`"))
                        create_statement = result.fetchone()[1]
                        f.write(f"DROP TABLE IF EXISTS `{table}`;\n")
                        f.write(f"{create_statement};\n\n")
                    elif db_uri.startswith('sqlite'):
                        result = conn.execute(text(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table}'"))
                        create_statement = result.fetchone()[0]
                        f.write(f"DROP TABLE IF EXISTS `{table}`;\n")
                        f.write(f"{create_statement};\n\n")
                    
                    # Get table data
                    result = conn.execute(text(f"SELECT * FROM `{table}`"))
                    columns = result.keys()
                    
                    if columns:
                        rows = result.fetchall()
                        if rows:
                            f.write(f"INSERT INTO `{table}` ({', '.join([f'`{col}`' for col in columns])}) VALUES\n")
                            
                            for i, row in enumerate(rows):
                                values = []
                                for value in row:
                                    if value is None:
                                        values.append('NULL')
                                    elif isinstance(value, str):
                                        values.append(f"'{value.replace(chr(39), chr(39)+chr(39))}'")
                                    elif isinstance(value, datetime.datetime):
                                        values.append(f"'{value.strftime('%Y-%m-%d %H:%M:%S')}'")
                                    else:
                                        values.append(str(value))
                                
                                f.write(f"({', '.join(values)})")
                                if i < len(rows) - 1:
                                    f.write(",\n")
                                else:
                                    f.write(";\n\n")
            
            # Re-enable foreign key checks
            f.write("SET FOREIGN_KEY_CHECKS = 1;\n")
        
        flash('Backup created successfully.', 'success')
    except Exception as e:
        flash(f'Backup failed: {e}', 'danger')
    
    return redirect(url_for('admin.backups'))



@admin.route('/backups/download/<filename>')
@login_required
@admin_required
def download_backup(filename):
    backup_dir = os.path.join(current_app.root_path, 'backups')
    backup_path = os.path.join(backup_dir, filename)
    if not os.path.exists(backup_path):
        flash('Backup file not found.', 'danger')
        return redirect(url_for('admin.backups'))
    return send_file(backup_path, as_attachment=True)

@admin.route('/backups/delete/<filename>', methods=['POST'])
@login_required
@admin_required
def delete_backup(filename):
    backup_dir = os.path.join(current_app.root_path, 'backups')
    backup_path = os.path.join(backup_dir, filename)
    if not os.path.exists(backup_path):
        flash('Backup file not found.', 'danger')
    else:
        try:
            os.remove(backup_path)
            flash('Backup deleted successfully.', 'success')
        except Exception as e:
            flash(f'Failed to delete backup: {e}', 'danger')
    return redirect(url_for('admin.backups'))