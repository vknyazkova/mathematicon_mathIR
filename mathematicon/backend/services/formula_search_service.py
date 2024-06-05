from abc import ABC, abstractmethod
from typing import List, Optional, Callable
import re

from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

from ..repositories.emebdding_repo import FormulaEmbeddingRepository
from ..model import FormulaAnnotation, RankedFormulas
from TangentCFT.tangent_cft.tangent_cft_parser import TangentCFTParser


class RerankingModel(ABC):
    @abstractmethod
    def rank(self, query: str, ranked_formulas: RankedFormulas) -> RankedFormulas:
        raise NotImplementedError


def node_extractor(tex_formula: str) -> List[str]:
    formula_tree_string = TangentCFTParser.get_math_tree(tex_formula, from_mathml=False, slt=False).tostring()
    return re.findall(r'(?<=\[)(.*?)(?=[,\]\[])', formula_tree_string)


class TFIDFRerankingModel(RerankingModel):
    def __init__(self, analyzer: Callable[[str], List[str]], tfidf_weight: float = 0.5):
        self.analyzer = analyzer
        self.tfidf_weight = tfidf_weight

    def rank(self, query: str, ranked_formulas: RankedFormulas) -> RankedFormulas:
        vectorizer = TfidfVectorizer(analyzer=self.analyzer)
        embeddings = vectorizer.fit_transform(ranked_formulas.formulas)
        query_embedding = vectorizer.transform([query])

        scores = query_embedding.dot(embeddings.T).toarray().flatten()
        scores = (scores - scores.min()) / (scores.max() - scores.min())
        original_scores = np.array(ranked_formulas.scores)
        new_scores = original_scores * (1 - self.tfidf_weight) + scores * self.tfidf_weight
        ranked_indices = np.argsort(new_scores)[::-1]
        ranked_formulas.ids = np.array(ranked_formulas.ids)[ranked_indices].tolist()
        ranked_formulas.formulas = np.array(ranked_formulas.formulas)[ranked_indices].tolist()
        ranked_formulas.scores = new_scores[ranked_indices].tolist()
        return ranked_formulas


class FormulaSearchService:
    def __init__(self,
                 formula_embeddings_repo: FormulaEmbeddingRepository,
                 reranker: Optional[RerankingModel] = None):
        self.embedding_repo = formula_embeddings_repo
        self.reranker = reranker

    def search(self, formula: str, top_n: int = 10, threshold: float = 0.4) -> List[FormulaAnnotation]:
        retrieved = self.embedding_repo.find_similar_formulas(formula, top_n=top_n)
        if self.reranker:
            retrieved = self.reranker.rank(formula, retrieved)
        under_threshold = np.array(retrieved.scores) >= threshold
        formula_annotations = []
        for i in range(under_threshold.sum()):
            formula_annotations.append(FormulaAnnotation(
                fragment_id=int(retrieved.ids[i]),
                tex_formula=retrieved.formulas[i],
            ))
        return formula_annotations
