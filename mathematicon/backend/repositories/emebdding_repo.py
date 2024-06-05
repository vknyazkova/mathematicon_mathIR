from typing import Dict, List

import numpy as np
from chromadb import PersistentClient, EmbeddingFunction, Documents, Embeddings

from ..model import FormulaAnnotation, RankedFormulas
from TangentCFT.tangent_cft.tangent_cft_parser import TangentCFTParser
from TangentCFT.tangent_cft.tangent_cft_back_end import TangentCFTBackEnd


class TangentCFTEmbedding(EmbeddingFunction[Documents]):
    def __init__(self,
                 tangent_cft: TangentCFTBackEnd,
                 mathml: bool = False,
                 slt: bool = False
                 ):
        self.tangent_cft = tangent_cft
        self.tangent_cft_parser = TangentCFTParser()
        self.mathml = mathml
        self.slt = slt

    def __call__(self, input: Documents) -> Embeddings:
        embeds = []
        for formula in input:
            formula_tree_tuples = self.tangent_cft_parser.parse(formula, mathml=self.mathml, slt=self.slt)
            embeds.append(self.tangent_cft.get_formula_emebedding(formula_tree_tuples).tolist())
        return embeds


class FormulaEmbeddingRepository:
    def __init__(self,
                 chroma_path: str,
                 emb_function: EmbeddingFunction,
                 collection_name: str = 'formulas'):
        self.chroma_client = PersistentClient(chroma_path)
        self.collection = self.chroma_client.get_or_create_collection(collection_name, embedding_function=emb_function, metadata={"hnsw:space": "cosine"})

    def add_formula(self, formula: FormulaAnnotation):
        assert getattr(formula, 'fragment_id', None) is not None
        self.collection.upsert(ids=[str(formula.fragment_id)], documents=[formula.tex_formula])

    def delete_formula(self, formula: FormulaAnnotation):
        assert getattr(formula, 'fragment_id', None) is not None
        self.collection.delete(ids=[str(formula.fragment_id)])

    def find_similar_formulas(self, tex_formula: str, top_n: int = 10) -> RankedFormulas:
        result = self.collection.query(query_texts=[tex_formula], n_results=top_n, include=['documents', 'distances'])
        return RankedFormulas(
            ids=result['ids'][0],
            formulas=result['documents'][0],
            scores=((1 - np.array(result['distances'][0])) / 2).tolist()
        )

