from datetime import datetime
import pytz
from bartr import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

def malaysia_now():
    """Get current time in Malaysia timezone"""
    malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
    return datetime.now(malaysia_tz).replace(tzinfo=None)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255))
    name = db.Column(db.String(100))
    mobile_number = db.Column(db.String(20))
    region = db.Column(db.String(100), nullable=False)  # State in Malaysia
    city = db.Column(db.String(100), nullable=False)    # City in Malaysia
    profile_photo = db.Column(db.String(255))
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=malaysia_now)
    
    # Relationships
    items = db.relationship('Item', backref='owner', lazy=True)
    sent_trades = db.relationship('Trade', foreign_keys='Trade.sender_id', backref='sender', lazy=True)
    received_trades = db.relationship('Trade', foreign_keys='Trade.receiver_id', backref='receiver', lazy=True)
    reviews_given = db.relationship('Review', foreign_keys='Review.reviewer_id', backref='reviewer', lazy=True)
    reviews_received = db.relationship('Review', foreign_keys='Review.reviewed_id', backref='reviewed', lazy=True)
    favorites = db.relationship('Favorite', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_last_message(self, other_user_id):
        """Get the last message exchanged with another user."""
        return Message.query.filter(
            ((Message.sender_id == self.id) & (Message.receiver_id == other_user_id)) |
            ((Message.sender_id == other_user_id) & (Message.receiver_id == self.id))
        ).order_by(Message.created_at.desc()).first()

    @property
    def avg_rating(self):
        """Calculate average rating from received reviews."""
        reviews = self.reviews_received
        if not reviews:
            return 0
        return round(sum(review.rating for review in reviews) / len(reviews), 1)

    @property
    def review_count(self):
        """Get total number of reviews received."""
        return len(self.reviews_received)

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    condition = db.Column(db.String(50))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    estimated_value = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=malaysia_now)
    is_active = db.Column(db.Boolean, default=True)
    is_flagged = db.Column(db.Boolean, default=False)
    
    # Relationships
    photos = db.relationship('ItemPhoto', backref='item', lazy=True, order_by='ItemPhoto.order')
    favorites = db.relationship('Favorite', backref='item', lazy=True)
    flags = db.relationship('Flag', backref='item', lazy=True)
    
    @property
    def is_traded(self):
        """Check if this item is involved in any completed trade"""
        # Check if item was requested in a completed trade
        completed_as_requested = Trade.query.filter_by(
            requested_item_id=self.id,
            status='completed'
        ).first()
        
        if completed_as_requested:
            return True
            
        # Check if item was offered in a completed trade
        completed_as_offered = db.session.query(Trade).join(TradeItem).filter(
            TradeItem.item_id == self.id,
            Trade.status == 'completed'
        ).first()
        
        return completed_as_offered is not None

    def calculate_fairness_score(self, other_items):
        """Calculate trade fairness score based on estimated values"""
        if not self.estimated_value:
            return None
        
        other_total_value = sum(item.estimated_value for item in other_items if item.estimated_value)
        if not other_total_value:
            return None
        
        # Calculate ratio (closer to 1.0 means more fair)
        ratio = min(self.estimated_value, other_total_value) / max(self.estimated_value, other_total_value)
        
        # Convert to percentage score (0-100)
        return round(ratio * 100)

class ItemPhoto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    photo_path = db.Column(db.String(255), nullable=False)
    order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=malaysia_now)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(255))
    order = db.Column(db.Integer, default=0)
    items = db.relationship('Item', backref='category', lazy=True)

class Trade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    requested_item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, accepted, rejected, cancelled, completed
    message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=malaysia_now)
    updated_at = db.Column(db.DateTime, default=malaysia_now, onupdate=malaysia_now)
    sender_completed = db.Column(db.Boolean, default=False)
    receiver_completed = db.Column(db.Boolean, default=False)
    sender_completed_at = db.Column(db.DateTime)
    receiver_completed_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    auto_completed = db.Column(db.Boolean, default=False)
    
    # Relationships
    offered_items = db.relationship('TradeItem', backref='trade', lazy=True)
    requested_item = db.relationship('Item', foreign_keys=[requested_item_id])
    reviews = db.relationship('Review', backref='trade', lazy=True)

    @property
    def fairness_score(self):
        """Calculate trade fairness score"""
        if not self.requested_item.estimated_value:
            return None
        
        offered_items = [trade_item.item for trade_item in self.offered_items]
        return self.requested_item.calculate_fairness_score(offered_items)

    @property
    def fairness_text(self):
        """Get text description of trade fairness"""
        score = self.fairness_score
        if score is None:
            return "Unable to calculate"
        elif score >= 85:
            return "Very Fair"
        elif score >= 70:
            return "Fair"
        elif score >= 50:
            return "Somewhat Fair"
        else:
            return "Unfair"

class TradeItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    trade_id = db.Column(db.Integer, db.ForeignKey('trade.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    item = db.relationship('Item')

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reviewed_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    trade_id = db.Column(db.Integer, db.ForeignKey('trade.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=malaysia_now)
    # Add relationship to review photos
    photos = db.relationship('ReviewPhoto', backref='review', lazy=True, cascade='all, delete-orphan')

class ReviewPhoto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    review_id = db.Column(db.Integer, db.ForeignKey('review.id'), nullable=False)
    photo_path = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=malaysia_now)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=malaysia_now)
    is_read = db.Column(db.Boolean, default=False)
    # Add relationship to message images
    images = db.relationship('MessageImage', backref='message', lazy=True, cascade='all, delete-orphan')

class MessageImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.Integer, db.ForeignKey('message.id'), nullable=False)
    image_path = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=malaysia_now)

class Favorite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=malaysia_now)

class Flag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    violation_type = db.Column(db.String(50), nullable=False, default='other')
    reason = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=malaysia_now)
    status = db.Column(db.String(20), default='pending')  # pending, resolved, dismissed
    
    # Relationships
    user = db.relationship('User', backref='flags', lazy=True) 

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # 'trade_proposal', 'flag'
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=malaysia_now)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=True)
    trade_id = db.Column(db.Integer, db.ForeignKey('trade.id'), nullable=True)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('notifications', lazy=True))
    item = db.relationship('Item', backref=db.backref('notifications', lazy=True))
    trade = db.relationship('Trade', backref=db.backref('notifications', lazy=True))

    def __repr__(self):
        return f'<Notification {self.type} for User {self.user_id}>' 