from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from config import Config
import os

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
mail = Mail()

def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)

    # Ensure the instance folder exists for the SQLite DB
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)

    # Register SQLite foreign key pragma
    from sqlalchemy import event
    from sqlalchemy.engine import Engine
    
    @event.listens_for(Engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        if app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite'):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.admin import bp as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    from app.teacher import bp as teacher_bp
    app.register_blueprint(teacher_bp, url_prefix='/teacher')

    from app.principal import bp as principal_bp
    app.register_blueprint(principal_bp, url_prefix='/principal')

    from app.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    # Root route redirects to login
    @app.route('/')
    def index():
        from flask import redirect, url_for
        return redirect(url_for('auth.login'))

    return app

from app import models