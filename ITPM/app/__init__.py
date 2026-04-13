from flask import Flask
from flask_login import LoginManager
from config import config
from app.models import db, User
import os

login_manager = LoginManager()

def create_app(config_name=None):
    """Application factory"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.main import main_bp
    from app.routes.employees import employees_bp
    from app.routes.projects import projects_bp
    from app.routes.allocations import allocations_bp
    from app.routes.admin import admin_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp, url_prefix='/')
    app.register_blueprint(employees_bp, url_prefix='/employees')
    app.register_blueprint(projects_bp, url_prefix='/projects')
    app.register_blueprint(allocations_bp, url_prefix='/allocations')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    @app.context_processor
    def inject_user():
        """Inject current user into template context"""
        from flask_login import current_user
        return {'current_user': current_user}
    
    return app
