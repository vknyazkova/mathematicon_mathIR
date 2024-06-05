import datetime
from urllib.error import HTTPError
import json

from flask import render_template, redirect, url_for, request
from flask_login import current_user

from .app import app, webdb, search_service, user_service
from ..backend.model import SearchHistory
from ..backend.models.mathtag_search import MathtagSearch

mathtag_search = MathtagSearch(webdb)


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
    # TODO: turn inception_id to string repr
    if current_user.is_authenticated:
        userid = current_user.user_info.user_id
        history = SearchHistory(
            user_id=userid,
            timestamp=datetime.datetime.now().isoformat(sep=' ', timespec='seconds'),
            query=query,
            link=request.url[request.url.rfind('/'):]
        )
        user_service.save_history(history)
        starring = "true"
    else:
        userid = None
        starring = "false"

    if request.args['search_type'] == 'lemma':
        query_info, sents_info = search_service.lemmaSearch(query)
        hide_cap = 'false'
    elif request.args['search_type'] == 'word':
        query_info, sents_info = search_service.exactMatchSearch(query)
        hide_cap = 'false'
    elif request.args['search_type'] == 'tag':
        query_info, sents_info = mathtag_search.search(query, userid)
        hide_cap = 'true'
    elif request.args['search_type'] == 'formula':
        query_info, sents_info = search_service.searchByFormula(json.dumps(query)[1:-1])
        hide_cap = 'true'
    else:
        raise HTTPError

    if current_user.is_authenticated:
        sents_info = user_service.personalise_search_results(current_user.user_info, search_results=sents_info)

    return render_template(
        "result2.html",
        main_lan=lang,
        query_info=query_info,
        sents_info=sents_info,
        query=query,
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
