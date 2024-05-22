from urllib.parse import parse_qs, urlparse, unquote

from flask import render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user

from ..backend.model import Favorites
from .user import User


from .app import app, user_service

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(username):
    user_info = user_service.get_by_username(username)
    if user_info is None:
        return None
    return User(user_info)


@app.route("/logout_<lang>")
@login_required
def logout(lang):
    logout_user()
    return redirect(url_for('main_page', lang=lang))


@app.route('/register_<lang>', methods=['GET', 'POST'])
def reg_page(lang):
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        existing_user = user_service.get_by_username(username)
        if existing_user:
            flash('User already exists.')
            return redirect(url_for('reg_page', lang=lang))

        user_info = user_service.create_user(username, password, email)
        login_user(User(user_info))
        flash('You\'ve been successfully logged-in')
        return render_template('account.html', main_lan=lang, login=current_user.username, email=current_user.email)
    return render_template('register.html', main_lan=lang)


@app.route('/login_<lang>', methods=['GET', 'POST'])
def login(lang):
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = load_user(username)
        if user and user_service.validate_password(user.user_info, password):
            login_user(user)
            return redirect(url_for('account', lang=lang))
        else:
            flash('Invalid username or password.')
            return redirect(url_for('login', lang=lang))

    return render_template('login.html', main_lan=lang)


@app.route('/account_<lang>', methods=['POST', 'GET'])
def account(lang):
    if not current_user.is_authenticated:
        return redirect(url_for('login', lang=lang))
    else:
        user_history = user_service.get_user_search_history(current_user.user_info)
        favs = user_service.get_user_favorites(current_user.user_info)
        return render_template('account.html',
                               main_lan=lang,
                               login=current_user.username,
                               email=current_user.email,
                               history_list=user_history,
                               favs=favs,
                               )


def query_name_from_url(url: str) -> str:
    # TODO: turn math tags inception id to string repr
    query = unquote(urlparse(url).query)
    return parse_qs(query).get('query')[0]


@login_required
@app.route('/favourites/', methods=['POST', 'GET'])
def remove_sent():
    user_request = request.get_json()
    if user_request.get('query_text', None):
        query_text = user_request['query_text']
    else:
        query_text = query_name_from_url(user_request['query_link'])
    favorites = Favorites(
        user_id=current_user.user_info.user_id,
        query=query_text,
        link=user_request['query_link'],
        sentence_id=user_request['id']
    )
    if user_request['method'] == 'add':
        user_service.add_favorites(favorites)
    elif user_request['method'] == 'delete':
        user_service.remove_favorites(favorites)
    return "blurp"
