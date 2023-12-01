from sqlite3 import IntegrityError
from urllib.parse import parse_qs

from flask import redirect, url_for, flash, request, render_template
from flask_login import LoginManager, login_required, login_user, logout_user, current_user

from .app import app
from .user import User
from ..backend.models.database import UserDBHandler
from .. import DB_PATH

login_manager = LoginManager()
login_manager.init_app(app)

user_db = UserDBHandler(DB_PATH)


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
        try:
            user_db.add_user(username, hashed_password, salt, email)
            flash('You\'ve been successfully logged-in')
            user = User(DB_PATH).get(username)
            login_user(user, remember=True)
            return render_template('account.html', main_lan=lang, login=current_user.username, email=current_user.email)

        except IntegrityError as e:  # если такой юзер уже есть в бд
            dupl_field = str(e).split()[-1].split('.')[-1]
            flash(f'The user with this {dupl_field} already exists')
            return redirect(url_for('reg_page', lang=lang))
    return render_template('register.html', main_lan=lang)


@app.route('/login_<lang>', methods=['GET', 'POST'])
def login(lang):
    if request.method == 'POST':
        un = request.form['username']
        user = User(DB_PATH).get(un)
        if user:
            if user.validate_password(request.form['password']):
                login_user(user, remember=True)
                flash(f'You\'ve been successfully logged-in')
                return redirect(url_for('account', lang=lang))
    return render_template('login.html', main_lan=lang)


def user_favs(userid):
    user_favs = user_db.get_user_favs(userid)
    favs = []
    for query_group in user_favs:
        query = query_group[1]
        if query_group[2] == 'tag':
            query = user_db.math_tag_ui_name(query)
        query_str = 'query=' + '+'.join(query.split(' ')) + '&' + 'search_type=' + query_group[2]
        sents_ids = query_group[3].split(';')
        sents = query_group[4].split(';')
        favs.append((query_group[0], query, query_str, list(zip(sents_ids, sents))))
    return favs


def user_history_list(userid: int):
    user_queries = user_db.get_user_history(userid)
    history_list = []
    for q in user_queries:
        parsed = parse_qs(q)
        query = parsed["query"][0]
        if parsed["search_type"][0] == "tag":
            query = user_db.math_tag_ui_name(query)
        history_list.append((query, q))
    return history_list


@app.route('/account_<lang>', methods=['POST', 'GET'])
def account(lang):
    if not current_user.is_authenticated:
        return redirect(url_for('login', lang=lang))
    else:
        user_history = user_history_list(current_user.id)
        favs = user_favs(userid=current_user.id)
        return render_template('account.html',
                               main_lan=lang,
                               login=current_user.username,
                               email=current_user.email,
                               history_list=user_history,
                               favs=favs,
                               )


@login_required
@app.route('/favourites/', methods=['POST', 'GET'])
def remove_sent():
    user_request = request.get_json()
    if user_request['method'] == 'add':
        query = ' '.join(user_request['query'].split('+'))
        query_type = user_request['search_type']
        user_db.add_favs(current_user.id, query=query, query_type=query_type, sent_id=user_request['id'])
    elif user_request['method'] == 'delete':
        user_db.remove_fav(current_user.id, user_request['id'])
    return "blurp"