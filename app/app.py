from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    prix = db.Column(db.Float, nullable=False)

class Cagnotte(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    montant = db.Column(db.Float, default=0.0)



@app.route("/")
def index():
    items = Item.query.all()
    cagnotte = Cagnotte.query.first()
    if not cagnotte:
        cagnotte = Cagnotte(montant=0.0)
        db.session.add(cagnotte)
        db.session.commit()

    total = sum(item.prix for item in items)
    objectif_atteint = cagnotte.montant >= total and total > 0

    return render_template("index.html", wishlist=items, cagnotte=cagnotte.montant, total=total, objectif_atteint=objectif_atteint)

@app.route("/add_item", methods=["POST"])
def add_item():
    nom = request.form.get("nom")
    prix = float(request.form.get("prix"))
    db.session.add(Item(nom=nom, prix=prix))
    db.session.commit()
    return redirect(url_for("index"))

@app.route("/add_money", methods=["POST"])
def add_money():
    montant = float(request.form.get("montant"))
    cagnotte = Cagnotte.query.first()
    cagnotte.montant += montant
    db.session.commit()
    return redirect(url_for("index"))

@app.route("/delete_item/<int:id>")
def delete_item(id):
    item = Item.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for("index"))

@app.route("/edit_money", methods=["POST"])
def edit_money():
    nouveau_montant = float(request.form.get("nouveau_montant"))
    cagnotte = Cagnotte.query.first()
    cagnotte.montant = nouveau_montant
    db.session.commit()
    return redirect(url_for("index"))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
