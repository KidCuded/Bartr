import os
from datetime import datetime, timedelta
import pytz

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS 

def init_jinja_filters(app):
    @app.template_filter('malaysia_time')
    def malaysia_time(value):
        """Convert UTC time to Malaysia time."""
        if value is None:
            return ""
        malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
        # Ensure the datetime is timezone-aware
        if value.tzinfo is None:
            value = pytz.UTC.localize(value)
        return value.astimezone(malaysia_tz)

    @app.template_filter('format_date')
    def format_date(value):
        """Format date in Malaysia timezone."""
        if value is None:
            return ""
        malaysia_time = value
        if value.tzinfo is None:
            malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
            malaysia_time = pytz.UTC.localize(value).astimezone(malaysia_tz)
        return malaysia_time.strftime('%d %B %Y')

    @app.template_filter('format_time')
    def format_time(value):
        """Format time in Malaysia timezone."""
        if value is None:
            return ""
        malaysia_time = value
        if value.tzinfo is None:
            malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
            malaysia_time = pytz.UTC.localize(value).astimezone(malaysia_tz)
        return malaysia_time.strftime('%H:%M')

    @app.template_filter('is_today')
    def is_today(value):
        """Check if date is today in Malaysia timezone."""
        if value is None:
            return False
        malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
        if value.tzinfo is None:
            value = pytz.UTC.localize(value)
        value_my = value.astimezone(malaysia_tz)
        now_my = datetime.now(malaysia_tz)
        return value_my.date() == now_my.date()

    @app.template_filter('is_yesterday')
    def is_yesterday(value):
        """Check if date is yesterday in Malaysia timezone."""
        if value is None:
            return False
        malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
        if value.tzinfo is None:
            value = pytz.UTC.localize(value)
        value_my = value.astimezone(malaysia_tz)
        now_my = datetime.now(malaysia_tz)
        yesterday = now_my - timedelta(days=1)
        return value_my.date() == yesterday.date() 