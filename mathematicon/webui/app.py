from pathlib import Path

from flask import Flask
import spacy

from .secret import FLASK_SECRET_KEY
from .. import DB_PATH
from ..backend.models.text_search import TextSearch
from ..backend.models.database import WebDBHandler


app = Flask(__name__)
app.config['SECRET_KEY'] = FLASK_SECRET_KEY

nlp = spacy.load('ru_core_news_sm')
print(DB_PATH)
db = WebDBHandler(DB_PATH)


@app.route('/')
def hello_world():  # put application's code here
    return 'Hello World!'


if __name__ == '__main__':
    text_search = TextSearch(db, nlp)
    print(db.sent_context(1, 2))
    app.run()
