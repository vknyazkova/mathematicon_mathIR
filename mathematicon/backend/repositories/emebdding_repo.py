from chromadb import Client, EmbeddingFunction

from ..model import FormulaAnnotation


class FormulaEmbeddingRepository:
    def __init__(self,
                 chroma_client: Client,
                 emb_function: EmbeddingFunction,
                 collection_name: str = 'formulas'):
        self.chroma_client = chroma_client
        self.collection = self.chroma_client.get_or_create_collection(collection_name, embedding_function=emb_function)

    def add_formula(self, formula: FormulaAnnotation) -> FormulaAnnotation:
        self.collection.upsert({'ids': [str(formula.fragment_id)], 'documents': [formula.tex_formula]})
        self.collection.get()
