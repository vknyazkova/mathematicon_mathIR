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
    if current_user.is_authenticated:
        userid = current_user.id
    else:
        userid = None
    query_info, sents_info = text_search.search(query, userid)
    return render_template('result.html', main_lan=lang, query_info=query_info, sents_info=sents_info,
                           query=query, authorized=True)



