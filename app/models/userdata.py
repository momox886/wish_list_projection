from .. import db

class UserData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    salaire_mensuel = db.Column(db.Float, default=0.0)
    depenses_mensuelles = db.Column(db.Float, default=0.0)
