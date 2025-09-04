from flask import Blueprint
from bartr.models import Review
from datetime import datetime

main = Blueprint('main', __name__)

@main.app_template_filter('has_reviewed')
def has_reviewed(trade_id, user_id):
    """Check if a user has already reviewed a trade."""
    return Review.query.filter_by(trade_id=trade_id, reviewer_id=user_id).first() is not None

@main.app_template_filter('review_period_expired')
def review_period_expired(completed_at):
    """Check if review period (30 days) has expired."""
    if not completed_at:
        return False
    time_since_completion = datetime.utcnow() - completed_at
    return time_since_completion.days > 30

from bartr.main import routes 