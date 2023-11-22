from flask import render_template, redirect, url_for, request
from flask_login import current_user, login_required


from .app import app, nlp, webdb
from ..backend.models.text_search import TextSearch

text_search = TextSearch(webdb, nlp)


@app.route('/')
def start_page():
    return redirect(url_for('main_page', lang="en"))


@app.route('/main_<lang>')
def main_page(lang):
    return render_template('home.html', main_lan=lang)


@app.route('/result_<lang>', methods=['GET'])
def result(lang):
    # func to redirect and get search params
    if current_user.is_authenticated:
        userid = current_user.id
    else:
        userid = None
    query = request.args['query']

    if request.args['query_type'] == 'text':
        search_type = request.args.get('search_type', 'lemma')
        query_info, sents_info = text_search.search(query, userid, search_type)
    elif request.args['query_type'] == 'formula':
        raise NotImplementedError

    return render_template(
        "result.html",
        main_lan=lang,
        query_info=query_info,
        sents_info=sents_info,
        query=query,
        authorized=True,
    )
    # if request.form['query_type'] == "By text":
    #     user_request = request.form['query']
    # else:
    #     user_request = "вы ввели формулу"
    # return redirect(url_for('result_page', lang=lang, query=user_request))


# @app.route('/<query>_<lang>')
# def result_page(query, lang, ):
#     if current_user.is_authenticated:
#         userid = current_user.id
#     else:
#         userid = None
#     query_info, sents_info = text_search.search(query, userid)
#     return render_template('result.html', main_lan=lang, query_info=query_info, sents_info=sents_info,
#                            query=query, authorized=True)


@app.route('/help_<lang>')
def help_page(lang):
    # some func() to find POS tags
    poses = list()
    example_email = "corpus.mathematicon@gmail.com"
    example_tg_account = "@example"
    return render_template('help.html', main_lan=lang, POS_tags=poses, example_email=example_email,
                           example_tg_account=example_tg_account)
