from .. import db

class Budget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    salaire = db.Column(db.Float, nullable=False)
    depenses = db.Column(db.Float, nullable=False)
