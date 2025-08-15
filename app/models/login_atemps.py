from .. import db
from datetime import datetime
import pytz


def now_paris():
    paris_tz = pytz.timezone('Europe/Paris')
    return datetime.now(paris_tz)
class LoginAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    identifier = db.Column(db.String(150))  # email ou username tenté
    success = db.Column(db.Boolean, nullable=False)
    ip_address = db.Column(db.String(45))  # compatible IPv6
    timestamp = db.Column(db.DateTime, default=now_paris)