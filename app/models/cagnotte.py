from .. import db


class Cagnotte(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    montant = db.Column(db.Float, default=0.0)