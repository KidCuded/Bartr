from flask import render_template, url_for, flash, redirect, request, current_app, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlparse
from bartr import db
from bartr.models import User, Review, Item, Message, Notification, malaysia_now
from bartr.auth import auth
from bartr.auth.forms import LoginForm, RegistrationForm, UpdateProfileForm, ChangePasswordForm, MALAYSIA_CITIES
from werkzeug.utils import secure_filename
import os
import traceback
from datetime import datetime, timezone

@auth.context_processor
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

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    # Check if user is being redirected from add item button
    next_page = request.args.get('next')
    if next_page and 'new_item' in next_page:
        flash('Please log in to add an item to the trading platform.', 'info')
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid email or password', 'danger')
            return redirect(url_for('auth.login'))
        
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        
        # If user is admin, always redirect to admin dashboard
        if user.is_admin:
            next_page = url_for('admin.dashboard')
        elif not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('main.index')
        
        return redirect(next_page)
    
    return render_template('auth/login.html', title='Sign In', form=form)

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RegistrationForm()
    if request.method == 'POST':
        # Update city choices based on selected region
        if form.region.data in MALAYSIA_CITIES:
            form.city.choices = [('', 'Select City')] + [(city, city) for city in MALAYSIA_CITIES[form.region.data]]
    
    if form.validate_on_submit():
        try:
            user = User(
                username=form.username.data,
                email=form.email.data,
                name=form.name.data,
                region=form.region.data,
                city=form.city.data
            )
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            
            flash('Congratulations, you are now a registered user!', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            print("Registration error:", str(e))
            print(traceback.format_exc())
            flash('An error occurred during registration. Please try again.', 'danger')
            return render_template('auth/register.html', title='Register', form=form, MALAYSIA_CITIES=MALAYSIA_CITIES)
    
    return render_template('auth/register.html', title='Register', form=form, MALAYSIA_CITIES=MALAYSIA_CITIES)

@auth.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@auth.route('/profile')
@auth.route('/profile/<int:user_id>')
@login_required
def profile(user_id=None):
    if user_id is None:
        user = current_user
    else:
        user = User.query.get_or_404(user_id)
    
    # Get user's reviews
    reviews = Review.query.filter_by(reviewed_id=user.id).order_by(Review.created_at.desc()).all()
    
    # Calculate average rating
    avg_rating = 0
    review_count = len(reviews)
    if review_count > 0:
        avg_rating = sum(review.rating for review in reviews) / review_count
    
    # Use Malaysian time for consistency
    current_time = malaysia_now()
    days_since = (current_time - user.created_at).days
    
    # Calculate years and months
    years = days_since // 365
    remaining_days = days_since % 365
    months = remaining_days // 30
    days = remaining_days % 30
    
    time_display = ""
    if years > 0:
        time_display = f"{years}y"
        if months > 0:
            time_display += f" {months}m"
    elif months > 0:
        time_display = f"{months}m"
    else:
        time_display = f"{days}d"
    
    # Get user's items and sort by traded status manually (untraded first, then traded)
    all_items = Item.query.filter_by(user_id=user.id, is_active=True).order_by(
        Item.created_at.desc()
    ).all()
    
    # Separate traded and untraded items
    untraded_items = [item for item in all_items if not item.is_traded]
    traded_items = [item for item in all_items if item.is_traded]
    
    # Combine with untraded first
    items = untraded_items + traded_items
    
    return render_template('auth/profile.html', 
                         title='Profile', 
                         user=user,
                         items=items, 
                         reviews=reviews,
                         avg_rating=avg_rating,
                         review_count=review_count,
                         time_display=time_display)

@auth.route('/profile/<int:user_id>/reviews')
@auth.route('/profile/reviews')
def profile_reviews(user_id=None):
    if user_id is None:
        user = current_user
    else:
        user = User.query.get_or_404(user_id)
    
    # Get user's reviews
    reviews = Review.query.filter_by(reviewed_id=user.id).order_by(Review.created_at.desc()).all()
    
    # Calculate average rating
    avg_rating = 0
    review_count = len(reviews)
    if review_count > 0:
        avg_rating = sum(review.rating for review in reviews) / review_count
    
    # Get user's items for the profile template
    all_items = Item.query.filter_by(user_id=user.id, is_active=True).order_by(
        Item.created_at.desc()
    ).all()
    
    # Separate traded and untraded items
    untraded_items = [item for item in all_items if not item.is_traded]
    traded_items = [item for item in all_items if item.is_traded]
    
    # Combine with untraded first
    items = untraded_items + traded_items
    
    # Calculate time display (same as profile route)
    current_time = malaysia_now()
    days_since = (current_time - user.created_at).days
    
    years = days_since // 365
    remaining_days = days_since % 365
    months = remaining_days // 30
    days = remaining_days % 30
    
    time_display = ""
    if years > 0:
        time_display = f"{years}y"
        if months > 0:
            time_display += f" {months}m"
    elif months > 0:
        time_display = f"{months}m"
    else:
        time_display = f"{days}d"
    
    return render_template('auth/profile.html', 
                         title=f'{user.username} - Reviews', 
                         user=user, 
                         items=items,
                         reviews=reviews,
                         avg_rating=avg_rating,
                         review_count=review_count,
                         time_display=time_display)

@auth.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = UpdateProfileForm()
    if request.method == 'POST':
        # Update city choices based on selected region
        if form.region.data in MALAYSIA_CITIES:
            form.city.choices = [('', 'Select City')] + [(city, city) for city in MALAYSIA_CITIES[form.region.data]]
    
    if form.validate_on_submit():
        try:

            # Handle profile photo upload
            if form.profile_photo.data and form.profile_photo.data.filename:
                try:
                    # Delete old profile photo if it exists
                    if current_user.profile_photo:
                        old_photo_path = os.path.join(current_app.root_path, 'static', 'uploads', 'profile_photos', current_user.profile_photo)
                        if os.path.exists(old_photo_path):
                            os.remove(old_photo_path)
                    
                    # Save new photo
                    filename = secure_filename(form.profile_photo.data.filename)
                    timestamp = int(malaysia_now().timestamp())
                    filename = f"{timestamp}_{filename}"  # Add timestamp to prevent filename conflicts
                    
                    # Create the upload directory if it doesn't exist
                    upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'profile_photos')
                    os.makedirs(upload_dir, exist_ok=True)
                    
                    # Save the file
                    file_path = os.path.join(upload_dir, filename)
                    form.profile_photo.data.save(file_path)
                    
                    # Update database with new filename
                    current_user.profile_photo = filename
                    db.session.add(current_user)  # Explicitly add the user object for update
                except Exception as e:
                    current_app.logger.error(f"Error saving profile photo: {str(e)}")
                    flash('Failed to save profile photo. Other profile changes were saved.', 'warning')
        
            # Update other user information
            current_user.username = form.username.data
            current_user.name = form.name.data
            current_user.email = form.email.data
            current_user.mobile_number = form.mobile_number.data
            current_user.region = form.region.data
            current_user.city = form.city.data
            
            # Ensure changes are saved
            db.session.add(current_user)
            db.session.commit()
            
            flash('Your profile has been updated.', 'success')
            return redirect(url_for('auth.profile'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating profile: {str(e)}")
            flash('An error occurred while updating your profile. Please try again.', 'danger')
            return redirect(url_for('auth.edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.name.data = current_user.name
        form.email.data = current_user.email
        form.mobile_number.data = current_user.mobile_number
        form.region.data = current_user.region
        form.city.data = current_user.city
        # Update city choices based on current region
        if current_user.region in MALAYSIA_CITIES:
            form.city.choices = [('', 'Select City')] + [(city, city) for city in MALAYSIA_CITIES[current_user.region]]
    
    return render_template('auth/edit_profile.html', title='Edit Profile', form=form, MALAYSIA_CITIES=MALAYSIA_CITIES)

@auth.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash('Current password is incorrect.', 'danger')
            return redirect(url_for('auth.change_password'))
        
        current_user.set_password(form.new_password.data)
        db.session.commit()
        flash('Your password has been updated successfully.', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/change_password.html', title='Change Password', form=form)

@auth.route('/get_cities/<state>')
def get_cities(state):
    if state in MALAYSIA_CITIES:
        cities = MALAYSIA_CITIES[state]
        return jsonify([{'id': city, 'name': city} for city in cities])
    return jsonify([]) 