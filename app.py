import os
from flask import Flask

# Import models first (db is initialized in models module)
from models import db

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available, continue without it
    pass

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///baign_mart.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = 'static/uploads'
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    
    # Initialize extensions
    db.init_app(app)
    
    # Import flask_migrate only when needed
    try:
        from flask_migrate import Migrate
        migrate = Migrate(app, db)
    except ImportError:
        # flask_migrate is not available, continue without it
        migrate = None
    
    # Register blueprints
    from main import bp as main_bp
    app.register_blueprint(main_bp)
    
    from admin import bp as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin-pn')
    
    # Create upload directory if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    return app, db