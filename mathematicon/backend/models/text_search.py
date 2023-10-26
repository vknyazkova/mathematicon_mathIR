from typing import Iterable, Dict, Union, Tuple
import re

from spacy import Language

from .custom_dataclasses import HTMLsentence, QueryInfo, HTMLWord
from .database import WebDBHandler


class TextSearch:
    def __init__(self,
                 db: WebDBHandler,
                 nlp: Language):
        self.db = db
        self.nlp = nlp

        ...

    def create_query_info(self,
                          query: str) -> QueryInfo:
        query_info = QueryInfo()
        for t in self.nlp(query):
            token = HTMLWord(text=t.text,
                             html_type='plain',
                             pos=t.pos_,
                             lemma=t.lemma_,
                             color=self.color_query_token(t.text))
            query_info.tokens.append(token)
        return query_info


    def color_query_token(self,
                          token: str) -> str:
        return 'black'


    def select_sentences(self,
                         lemmatized_query: Iterable[str]) -> Iterable[Tuple[int,
                                                                            Iterable[Tuple[int, int]]]]:
        similar_sents = self.db.sents_with_query_words(lemmatized_query)
        reg_ex = r"\s?([А-Яа-яёЁ]+)?\s?".join(lemmatized_query)  # можно одно слово между не из запроса
        reg_ex = r"((?<=^)|(?<=\s))" + reg_ex + r"(?=$|\s)"  # чтобы не находились в середине слова
        matching_sents = []
        for sent in similar_sents:
            matches = []
            for m in re.finditer(reg_ex, sent['lemmatized']):
                matches.append(m.span())
            if matches:
                matching_sents.append((sent['id'], matches))
        return matching_sents

    def create_html_sentences(self,
                              selected_sents):
        ...


    def search(self,
               query: str) -> HTMLsentence:
        query_info = self.create_query_info(query)
        matching_sents = self.select_sentences([t.lemma for t in query_info.tokens])
        ...

