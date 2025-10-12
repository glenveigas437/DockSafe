import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
jwt = JWTManager()


@login_manager.user_loader
def load_user(user_id):
    from app.models import User

    return User.query.get(int(user_id))


def create_app(config_name=None):
    """Application factory pattern"""
    app = Flask(__name__)

    # Configuration
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")

    if config_name == "production":
        app.config.from_object("app.config.ProductionConfig")
    elif config_name == "testing":
        app.config.from_object("app.config.TestingConfig")
    else:
        app.config.from_object("app.config.DevelopmentConfig")

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    jwt.init_app(app)

    # Register blueprints
    from app.main import bp as main_bp

    app.register_blueprint(main_bp)

    from app.auth import bp as auth_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")

    from app.scanner import bp as scanner_bp

    app.register_blueprint(scanner_bp, url_prefix="/scanner")

    from app.reports import bp as reports_bp

    app.register_blueprint(reports_bp, url_prefix="/reports")

    from app.notifications import bp as notifications_bp

    app.register_blueprint(notifications_bp, url_prefix="/notifications")

    from app.dashboard import bp as dashboard_bp

    app.register_blueprint(dashboard_bp, url_prefix="/dashboard")

    from app.groups import bp as groups_bp

    app.register_blueprint(groups_bp, url_prefix="/groups")

    from app.api import bp as api_bp

    app.register_blueprint(api_bp, url_prefix="/api/v1")

    # Context processors
    @app.context_processor
    def inject_user_info():
        from flask import session

        user_id = session.get("user_id")
        if user_id:
            from app.models import User

            user = User.query.get(user_id)
            if user:
                # Check if user is admin/owner in any group
                user_is_admin = any(
                    user.get_role_in_group(group.id) in ["admin", "owner"]
                    for group in user.groups
                )
                return {
                    "user_is_admin": user_is_admin,
                    "user_groups": list(user.groups),
                    "selected_group_id": session.get("selected_group_id"),
                }
        return {"user_is_admin": False, "user_groups": [], "selected_group_id": None}

    # Create database tables
    with app.app_context():
        db.create_all()

    return app


from app import models
