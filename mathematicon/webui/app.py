from flask import Flask
import spacy

from .secret import FLASK_SECRET_KEY
from .. import DB_PATH, DATA_PATH, ENCODER, FT_MODEL
from ..backend.models.database import WebDBHandler

from ..backend.repositories.user_repo import UserRepository
from ..backend.repositories.transcript_repo import TranscriptRepository
from ..backend.repositories.lecture_repo import LectureRepository
from ..backend.repositories.annotation_repo import AnnotationRepository
from ..backend.repositories.emebdding_repo import FormulaEmbeddingRepository, TangentCFTEmbedding

from ..backend.services.user_service import UserService
from ..backend.services.lecture_transcript_service import LectureTranscriptService
from ..backend.services.formula_annotation_service import FormulaAnnotationService
from ..backend.services.search_service import SearchService
from ..backend.services.formula_search_service import FormulaSearchService, TFIDFRerankingModel, node_extractor

from TangentCFT.tangent_cft.tangent_cft_back_end import TangentCFTBackEnd

app = Flask(__name__)
app.config['SECRET_KEY'] = FLASK_SECRET_KEY

nlp = spacy.load('ru_core_news_sm')
webdb = WebDBHandler(DB_PATH)

user_repo = UserRepository(DB_PATH)
lecture_repo = LectureRepository(DB_PATH)
transcript_repo = TranscriptRepository(DB_PATH)
annotation_repo = AnnotationRepository(DB_PATH)

tangent_cft = TangentCFTBackEnd.load(encoder_map_path=ENCODER, ft_model_path=FT_MODEL)
embedder = TangentCFTEmbedding(tangent_cft=tangent_cft, mathml=False, slt=False)
emebding_repo = FormulaEmbeddingRepository(str(DATA_PATH), emb_function=embedder)

user_service = UserService(user_repository=user_repo, transcript_repository=transcript_repo)
transcript_service = LectureTranscriptService(transcript_repo, nlp)
formula_service = FormulaAnnotationService(
    lecture_repo=lecture_repo,
    transcript_repo=transcript_repo,
    annotation_repo=annotation_repo,
    formula_embeddings_repo=emebding_repo
)
reranker = TFIDFRerankingModel(analyzer=node_extractor, tfidf_weight=0.3)
formula_search_service = FormulaSearchService(emebding_repo, reranker)
search_service = SearchService(nlp, transcript_service, formula_service, formula_search_service)