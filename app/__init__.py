from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_mail import Mail
from datetime import timedelta
import os
from dotenv import load_dotenv
from flask_migrate import Migrate
from sqlalchemy import event
load_dotenv()


db = SQLAlchemy()
login_manager = LoginManager()
limiter = Limiter(key_func=get_remote_address)
mail = Mail()  # ✅ Nouveau : initialisation globale
mdp = os.getenv('MDP')
sec_key = os.getenv('SEC_KEY')
migrate = Migrate()

def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = sec_key 
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=10)

    # ✅ Configuration Flask-Mail
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = 'no.reply.weby.mapy@gmail.com'  # ← remplace par ton email
    app.config['MAIL_PASSWORD'] = f'{mdp}'  # ← mot de passe d'application Gmail
    app.config['MAIL_DEFAULT_SENDER'] = 'tonemail@gmail.com'

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    limiter.init_app(app)
    mail.init_app(app)  # ✅ Initialisation de Flask-Mail

    

    from .models import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from .routes.main import main
    from .auth.auth import auth

    app.register_blueprint(main)
    app.register_blueprint(auth)

    from flask import render_template

    @app.errorhandler(429)
    def ratelimit_handler(e):
        return render_template("429.html", error=e), 429

    with app.app_context():
        @event.listens_for(db.engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        db.create_all()


    return app