from flask import Blueprint, render_template, request, redirect, url_for
from ..models import Item, Cagnotte, Budget, UserData
from flask_login import login_required
from .. import db

main = Blueprint('main', __name__)

@main.route("/")
def home():
    return render_template("home.html")

@main.route("/index", methods=["GET", "POST"])
@login_required
def index():
    items = Item.query.all()
    cagnotte = Cagnotte.query.first()
    if not cagnotte:
        cagnotte = Cagnotte(montant=0.0)
        db.session.add(cagnotte)
        db.session.commit()

    user_data = UserData.query.first()
    if not user_data:
        user_data = UserData(salaire_mensuel=0.0, depenses_mensuelles=0.0)
        db.session.add(user_data)
        db.session.commit()

    total = sum(item.prix for item in items)
    objectif_atteint = cagnotte.montant >= total and total > 0

    montant_epargnable = user_data.salaire_mensuel - user_data.depenses_mensuelles
    if montant_epargnable > 0 and total > 0:
        mois_necessaires = (total - cagnotte.montant) / montant_epargnable
        mois_necessaires = max(0, mois_necessaires)
    else:
        mois_necessaires = None

    return render_template(
        "index.html",
        wishlist=items,
        cagnotte=cagnotte.montant,
        total=total,
        objectif_atteint=objectif_atteint,
        montant_epargnable=montant_epargnable,
        mois_necessaires=mois_necessaires,
        salaire_mensuel=user_data.salaire_mensuel,
        depenses_mensuelles=user_data.depenses_mensuelles
    )



@main.route("/add_item", methods=["POST"])
@login_required
def add_item():
    nom = request.form.get("nom")
    prix = float(request.form.get("prix"))
    db.session.add(Item(nom=nom, prix=prix))
    db.session.commit()
    return redirect(url_for("main.index"))

@main.route("/add_money", methods=["POST"])
@login_required
def add_money():
    montant = float(request.form.get("montant"))
    cagnotte = Cagnotte.query.first()
    cagnotte.montant += montant
    db.session.commit()
    return redirect(url_for("main.index"))

@main.route("/delete_item/<int:id>")
@login_required
def delete_item(id):
    item = Item.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for("main.index"))

@main.route("/edit_money", methods=["POST"])
@login_required
def edit_money():
    nouveau_montant = float(request.form.get("nouveau_montant"))
    cagnotte = Cagnotte.query.first()
    cagnotte.montant = nouveau_montant
    db.session.commit()
    return redirect(url_for("main.index"))

@main.route("/set_budget", methods=["POST"])
@login_required
def set_budget():
    salaire = float(request.form.get("salaire"))
    depenses = float(request.form.get("depenses"))

    budget = Budget.query.first()
    if not budget:
        budget = Budget(salaire=salaire, depenses=depenses)
        db.session.add(budget)
    else:
        budget.salaire = salaire
        budget.depenses = depenses
    
    db.session.commit()
    return redirect(url_for("main.index"))


@main.route("/update_finances", methods=["POST"])
@login_required
def update_finances():
    salaire = float(request.form.get("salaire_mensuel", 0))
    depenses = float(request.form.get("depenses_mensuelles", 0))
    user_data = UserData.query.first()
    if not user_data:
        user_data = UserData(salaire_mensuel=salaire, depenses_mensuelles=depenses)
        db.session.add(user_data)
    else:
        user_data.salaire_mensuel = salaire
        user_data.depenses_mensuelles = depenses
    db.session.commit()
    return redirect(url_for("main.index"))
