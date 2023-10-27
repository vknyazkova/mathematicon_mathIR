from flask import Flask
import spacy

from .secret import FLASK_SECRET_KEY
from .. import DB_PATH
from ..backend.models.database import WebDBHandler

app = Flask(__name__)
app.config['SECRET_KEY'] = FLASK_SECRET_KEY

nlp = spacy.load('ru_core_news_sm')
webdb = WebDBHandler(DB_PATH)

