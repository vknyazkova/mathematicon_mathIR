from urllib.parse import unquote

from flask import render_template, redirect, url_for, request
from flask_login import current_user, login_required

from .app import app, nlp, webdb
from ..backend.models.text_search import TextSearch
from ..backend.models.mathtag_search import MathtagSearch
from ..backend.models.database import UserDBHandler
from .. import DB_PATH

text_search = TextSearch(webdb, nlp)
mathtag_search = MathtagSearch(webdb)
user_db = UserDBHandler(DB_PATH)


@app.route('/')
def start_page():
    return redirect(url_for('main_page', lang="en"))


@app.route('/main_<lang>')
def main_page(lang):
    available_tags = webdb.get_available_tags()
    return render_template('home.html', main_lan=lang, tags=available_tags)


@app.route('/result_<lang>', methods=['GET'])
def result(lang):
    # func to redirect and get search params
    query = request.args["query"]
    if current_user.is_authenticated:
        userid = current_user.id
        query_string = unquote(request.query_string.decode("utf-8"))
        user_db.add_history(userid, query_string)
        starring = "true"
    else:
        userid = None
        starring = "false"
    if request.args['search_type'] == 'lemma':
        search_type = request.args.get('search_type', 'lemma')
        query_info, sents_info = text_search.search(query, userid, search_type)
        hide_cap = 'false'
    elif request.args['search_type'] == 'tag':
        query_info, sents_info = mathtag_search.search(query, userid)
        hide_cap = 'true'
    return render_template(
        "result.html",
        main_lan=lang,
        query_info=query_info,
        sents_info=sents_info,
        query=query,
        authorized=True,
        starring=starring,
        hide_cap=hide_cap,
    )


@app.route('/help_<lang>')
def help_page(lang):
    poses = webdb.get_pos_info()
    example_email = "corpus.mathematicon@gmail.com"
    example_tg_account = "@example"
    return render_template('help.html', main_lan=lang, POS_tags=poses, example_email=example_email,
                           example_tg_account=example_tg_account)
