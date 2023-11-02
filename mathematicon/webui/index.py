from flask import render_template, redirect, url_for, request


from .app import app, nlp, webdb
from ..backend.models.text_search import TextSearch

text_search = TextSearch(webdb, nlp)


@app.route('/')
def start_page():
    return redirect(url_for('main_page', lang="en"))


@app.route('/main_<lang>')
def main_page(lang):
    return render_template('home.html', main_lan=lang)


@app.route('/result_<lang>', methods=['POST', 'GET'])
def result(lang):
    if request.form['type'] == "By text":
        user_request = request.form["query"]
        '''
        query_string = ' '.join([t.text for t in query_info.tokens])
        if sents_info != []:
            ex_sent = sents_info[0]
            sentence_string = ''.join([t.text for t in ex_sent.tokens])
            print(sentence_string)
            print(sents_info[0].tokens)
        '''
    else:
        user_request = "вы ввели формулу"
    return redirect(url_for('result_page', lang=lang, query=user_request))

@app.route('/<query>_<lang>')
def result_page(query, lang, ):
    query_info, sents_info = text_search.search(query)
    return render_template('result.html', main_lan=lang, query_info=query_info, sents_info=sents_info,
                           query=query, authorized=True)


@app.route('/favourites/', methods=['POST', 'GET'])
def remove_sent():
    user_request = request.get_json()
    #print(user_request['method'], user_request['id'])
    return "blurp"

@app.route('/help_<lang>')
def help_page(lang):
    # some func() to find POS tags
    poses = list()
    example_email = "corpus.mathematicon@gmail.com"
    example_tg_account = "@example"
    return render_template('help.html', main_lan=lang, POS_tags=poses, example_email=example_email,
                           example_tg_account=example_tg_account)