from pathlib import Path
from sqlite3 import IntegrityError

from flask import redirect, url_for, flash, request, render_template
from flask_login import LoginManager, login_required, login_user, logout_user, current_user

from .app import app
from .user import User
from ..backend.models.database import WebDBHandler
from ..config import DATA_PATH, DB_NAME

DB_PATH = Path(DATA_PATH, DB_NAME)

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User(DB_PATH).get(user_id)


@app.route("/logout_<lang>")
@login_required
def logout(lang):
    logout_user()
    return redirect(url_for('main_page', lang=lang))


@app.route('/register_<lang>', methods=['GET', 'POST'])
def reg_page(lang):
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        hashed_password, salt = User.hash_password(password)
        db = WebDBHandler(DB_PATH)
        try:
            db.add_user(username, hashed_password, salt, email)
            flash('You\'ve been successfully logged-in')
            user = User(DB_PATH).get(username)
            login_user(user, remember=True)
            return render_template('account.html', main_lan=lang, login=current_user.username, email=current_user.email)

        except IntegrityError as e:  # если такой юзер уже есть в бд
            dupl_field = str(e).split()[-1].split('.')[-1]
            flash(f'The user with this {dupl_field} already exists')
            return redirect(url_for('reg_page', lang=lang))
    return render_template('register.html', main_lan=lang)

