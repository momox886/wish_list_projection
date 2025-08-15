from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user
from ..models import User
from .. import db, limiter
from datetime import timedelta
from flask import request
from ..models import LoginAttempt
import pyotp
import qrcode
from PIL import Image, ImageDraw
import socket
import io
import base64
from flask_login import login_required, current_user
from itsdangerous import URLSafeTimedSerializer
from flask import current_app

from flask_mail import Message
from .. import mail  # mail = Mail() doit être global dans __init__.py






auth = Blueprint('auth', __name__)



@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        name = request.form['name']
        first_name = request.form['first_name']
        username = request.form['username']

        if User.query.filter_by(email=email).first():
            flash("Email déjà utilisé.")
            return redirect(url_for('auth.signup'))
        elif User.query.filter_by(username=username).first():
            flash("Nom d'utilisateur déjà utilisé.")
            return redirect(url_for('auth.signup'))
        hashed_pw = generate_password_hash(password)
        role = 'superadmin' if email == 'habibdiallo186@gmail.com' else 'user'
        new_user = User(email=email, password=hashed_pw, name=name, first_name=first_name, username=username, role=role)

        db.session.add(new_user)
        db.session.commit()
        flash("Compte créé. Connecte-toi maintenant.")
        return redirect(url_for('auth.login'))

    return render_template('signup.html')

@auth.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    if request.method == 'POST':
        identifier = request.form['identifier']
        password = request.form['password']
        # ✅ Récupère l’IP réelle, même derrière un proxy
        ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        if ip and ',' in ip:
            ip = ip.split(',')[0].strip()


        user = User.query.filter((User.email == identifier) | (User.username == identifier)).first()

        # par défaut, échec
        success = False

        if user and check_password_hash(user.password, password):
            if user.twofa_enabled:
                session['pre_2fa_user_id'] = user.id
                db.session.add(LoginAttempt(identifier=identifier, success=True, ip_address=ip))
                db.session.commit()
                return redirect(url_for('auth.verify_2fa'))
            else:
                login_user(user, remember=False, duration=timedelta(minutes=10))
                success = True
                flash("Connexion réussie.")
                db.session.add(LoginAttempt(identifier=identifier, success=True, ip_address=ip))
                db.session.commit()
                return redirect(url_for('main.index'))
        else:
            flash("Identifiant incorrect ou mot de passe incorrect.")
            db.session.add(LoginAttempt(identifier=identifier, success=False, ip_address=ip))
            db.session.commit()
            return render_template('login.html', identifier=identifier)

    return render_template('login.html')

@auth.route('/activate-2fa')
@login_required
def activate_2fa():
    if not current_user.twofa_secret:
        secret = pyotp.random_base32()
        current_user.twofa_secret = secret
        db.session.commit()
    else:
        secret = current_user.twofa_secret

    otp_uri = pyotp.totp.TOTP(secret).provisioning_uri(name=current_user.email, issuer_name="Webby App")

    # Générer QR code en base64
    img = qrcode.make(otp_uri)
    buf = io.BytesIO()
    img.save(buf)
    buf.seek(0)
    img_b64 = base64.b64encode(buf.read()).decode()

    return render_template('activate_2fa.html', img_b64=img_b64)

@auth.route('/confirm-2fa', methods=['POST'])
@login_required
def confirm_2fa():
    otp = request.form.get('otp')
    totp = pyotp.TOTP(current_user.twofa_secret)

    if totp.verify(otp):
        current_user.twofa_enabled = True
        db.session.commit()
        flash("2FA activé avec succès.")
        return redirect(url_for('main.index'))
    else:
        flash("Code invalide. Réessaie.")
        return redirect(url_for('auth.activate_2fa'))


@auth.route('/verify-2fa', methods=['GET', 'POST'])
def verify_2fa():
    user_id = session.get('pre_2fa_user_id')
    if not user_id:
        flash("Session expirée.")
        return redirect(url_for('auth.login'))

    user = User.query.get(user_id)

    if request.method == 'POST':
        otp = request.form.get('otp')
        if pyotp.TOTP(user.twofa_secret).verify(otp):
            login_user(user)
            session.pop('pre_2fa_user_id', None)
            flash("Connexion 2FA réussie.")
            return redirect(url_for('main.index'))
        else:
            flash("Code incorrect.")

    return render_template('verify_2fa.html')

@auth.route('/disable-2fa', methods=['GET', 'POST'])
@login_required
def disable_2fa():
    if request.method == 'POST':
        otp = request.form.get('otp')
        if pyotp.TOTP(current_user.twofa_secret).verify(otp):
            current_user.twofa_enabled = False
            current_user.twofa_secret = None
            db.session.commit()
            flash("Double authentification désactivée.")
            return redirect(url_for('main.index'))
        else:
            flash("Code incorrect.")
    return render_template('disable_2fa.html')


@auth.route('/security-settings')
@login_required
def security_settings():
    return render_template("security_settings.html", user=current_user)


def generate_reset_token(email):
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return s.dumps(email, salt='password-reset')

def verify_reset_token(token, expiration=3600):
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = s.loads(token, salt='password-reset', max_age=expiration)
    except Exception:
        return None
    return email


@auth.route('/reset-request', methods=['GET', 'POST'])
def reset_request():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()
        if user:
            token = generate_reset_token(user.email)
            reset_url = url_for('auth.reset_token', token=token, _external=True)

            msg = Message("Réinitialisation de votre mot de passe",
                          recipients=[user.email])
            msg.body = f"""Bonjour {user.first_name},

Vous avez demandé à réinitialiser votre mot de passe. Cliquez sur ce lien pour le faire :

{reset_url}

Si vous n'avez rien demandé, ignorez simplement ce message.

Bien cordialement,
L'équipe Webby
"""
            mail.send(msg)

        flash("Si un compte existe avec cette adresse, un lien a été envoyé.")
    return render_template('reset_request.html')


@auth.route('/reset/<token>', methods=['GET', 'POST'])
def reset_token(token):
    email = verify_reset_token(token)
    if not email:
        flash("Lien expiré ou invalide.")
        return redirect(url_for('auth.reset_request'))

    user = User.query.filter_by(email=email).first_or_404()

    if request.method == 'POST':
        new_password = request.form['password']
        confirm = request.form['confirm']

        if new_password != confirm:
            flash("Les mots de passe ne correspondent pas.")
            return redirect(request.url)

        user.password = generate_password_hash(new_password)
        db.session.commit()
        flash("Mot de passe mis à jour. Vous pouvez vous connecter.")
        return redirect(url_for('auth.login'))

    return render_template('reset_password.html')

@auth.route('/security-guide')
@login_required
def security_guide():
    """Page du guide de sécurité pour les utilisateurs"""
    return render_template('security_guide.html')
