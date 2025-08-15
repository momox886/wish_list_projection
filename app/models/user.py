from .. import db
import pyotp
from flask_login import UserMixin

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    username = db.Column(db.String(150), unique=True)
    name = db.Column(db.String(150))
    first_name = db.Column(db.String(150))
    password = db.Column(db.String(150))
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())
    role = db.Column(db.String(20), default='user') # Ajout du champ admin

    twofa_secret = db.Column(db.String(16))  # clef TOTP
    twofa_enabled = db.Column(db.Boolean, default=False)