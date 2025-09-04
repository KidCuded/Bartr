from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_socketio import SocketIO
from flask_mail import Mail
from flask_migrate import Migrate
from dotenv import load_dotenv
import os
import pytz
from .utils import init_jinja_filters

# Load environment variables
load_dotenv()

# Initialize Flask extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
socketio = SocketIO()
mail = Mail()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-change-this')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB max file size
    app.config['TIMEZONE'] = 'Asia/Kuala_Lumpur'
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)  # Initialize Flask-Migrate
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    socketio.init_app(app)
    mail.init_app(app)
    
    # Initialize custom Jinja filters
    init_jinja_filters(app)
    
    # Add timezone to Jinja globals
    app.jinja_env.globals.update(timezone=pytz.timezone(app.config['TIMEZONE']))
    
    # Register blueprints
    from bartr.auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)
    
    from bartr.main import main as main_blueprint
    app.register_blueprint(main_blueprint)
    
    from bartr.admin import admin as admin_blueprint
    app.register_blueprint(admin_blueprint, url_prefix='/admin')
    
    # Create upload folder if it doesn't exist
    os.makedirs(os.path.join(app.root_path, 'static', 'uploads'), exist_ok=True)
    
    return app 