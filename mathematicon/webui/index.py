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
        query_info, sents_info = text_search.search(user_request)

        ex_sent = sents_info[0]
        sentence_string = ''.join([t.text for t in ex_sent.tokens])
        print(sentence_string)
    else:
        user_request = "вы ввели формулу"
    return render_template('result.html', main_lan=lang, query_info=query_info, sents_info=sents_info)