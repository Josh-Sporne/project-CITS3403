from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from config import Config
from sqlalchemy import event
from sqlalchemy.engine import Engine

@event.listens_for(Engine, 'connect')
def set_sqlite_pragma(dbapi_connection, connection_record):
    try:
        cursor = dbapi_connection.cursor()
        cursor.execute('PRAGMA foreign_keys=ON')
        cursor.close()
    except Exception:
        pass

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'warning'
migrate = Migrate()
csrf = CSRFProtect()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp)

    from app.recipes import bp as recipes_bp
    app.register_blueprint(recipes_bp)

    from app.planner import bp as planner_bp
    app.register_blueprint(planner_bp)

    from app.ai import bp as ai_bp
    app.register_blueprint(ai_bp)

    from app.community import bp as community_bp
    app.register_blueprint(community_bp)

    from app.models import User

    @login_manager.user_loader
    def load_user(id):
        return db.session.get(User, int(id))

    @app.errorhandler(404)
    def not_found(e):
        return render_template('404.html'), 404

    @app.errorhandler(413)
    def file_too_large(e):
        from flask import flash, redirect, request, url_for
        flash('File too large — maximum size is 4 MB.', 'danger')
        return redirect(request.referrer or url_for('recipes.create')), 413

    @app.errorhandler(500)
    def server_error(e):
        return render_template('500.html'), 500

    @app.after_request
    def set_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        return response

    return app
