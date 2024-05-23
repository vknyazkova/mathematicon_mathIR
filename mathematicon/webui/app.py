from flask import Flask
import spacy

from .secret import FLASK_SECRET_KEY
from .. import DB_PATH
from ..backend.models.database import WebDBHandler

from ..backend.repositories.user_repo import UserRepository
from ..backend.repositories.transcript_repo import TranscriptRepository
from ..backend.repositories.lecture_repo import LectureRepository

from ..backend.services.user_service import UserService
from ..backend.services.lecture_transcript_service import LectureTranscriptService
from ..backend.services.search_service import SearchService

app = Flask(__name__)
app.config['SECRET_KEY'] = FLASK_SECRET_KEY

nlp = spacy.load('ru_core_news_sm')
webdb = WebDBHandler(DB_PATH)

user_repo = UserRepository(DB_PATH)
lecture_repo = LectureRepository(DB_PATH)
transcript_repo = TranscriptRepository(DB_PATH)

user_service = UserService(user_repository=user_repo, transcript_repository=transcript_repo)
transcript_service = LectureTranscriptService(transcript_repo, nlp)

search_service = SearchService(nlp, transcript_service)