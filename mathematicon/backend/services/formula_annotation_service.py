from typing import List

from ..repositories.emebdding_repo import FormulaEmbeddingRepository
from ..repositories.annotation_repo import AnnotationRepository
from ..model import FormulaAnnotation, AnnotationFragment


class FormulaAnnotationService:
    def __init__(self,
                 formula_embeddings_repo: FormulaEmbeddingRepository,
                 annotation_repo: AnnotationRepository,
                 embedding_model):
        self.embeddings_repo = formula_embeddings_repo
        self.annotation_repo = annotation_repo
        self.embedding_model = embedding_model

    def search_similar_formulas(self, formula: str) -> List[AnnotationFragment]:
        raise NotImplementedError

