from flask import Blueprint, render_template, request, redirect, url_for
from ..models import Item, Cagnotte
from .. import db

main = Blueprint('main', __name__)

@main.route("/")
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

@main.route("/add_item", methods=["POST"])
def add_item():
    nom = request.form.get("nom")
    prix = float(request.form.get("prix"))
    db.session.add(Item(nom=nom, prix=prix))
    db.session.commit()
    return redirect(url_for("main.index"))

@main.route("/add_money", methods=["POST"])
def add_money():
    montant = float(request.form.get("montant"))
    cagnotte = Cagnotte.query.first()
    cagnotte.montant += montant
    db.session.commit()
    return redirect(url_for("main.index"))

@main.route("/delete_item/<int:id>")
def delete_item(id):
    item = Item.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for("main.index"))

@main.route("/edit_money", methods=["POST"])
def edit_money():
    nouveau_montant = float(request.form.get("nouveau_montant"))
    cagnotte = Cagnotte.query.first()
    cagnotte.montant = nouveau_montant
    db.session.commit()
    return redirect(url_for("main.index"))
