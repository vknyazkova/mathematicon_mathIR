from typing import Iterable, Dict, Union, Tuple
import re

from spacy import Language

from .custom_dataclasses import HTMLsentence, QueryInfo, HTMLWord, HTMLSpan
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
        html_sentences = []
        for sent_id, match in selected_sents:
            html_sentence = HTMLsentence()
            sent_info = self.db.sent_info(sent_id)
            left, right = self.db.sent_context(sent_info['text_id'], sent_info['pos_in_text'])
            html_sentence.left = left
            html_sentence.right = right
            html_sentence.yb_link = self.create_yb_link(sent_info['youtube_link'], sent_info['timecode'])

            tokens = self.db.sent_token_info(sent_id)
            for t in self.html_tokens_generator(tokens):
                print(t)

        ...


    def html_tokens_generator(self,
                              tokens: Iterable[dict]):
        plain_token = HTMLSpan('')
        for token in tokens:
            if not token['pos'] == 'PUNCT':
                if plain_token.text:
                    yield plain_token
                    plain_token = HTMLSpan('')
                yield HTMLWord(text=token['token'],
                               pos=token['pos'],
                               lemma=token['lemma'])
            else:
                plain_token.text += token['token']
            whitespace = ' ' if token['whitespace'] else ''
            plain_token.text += whitespace

    @staticmethod
    def create_yb_link(video_link: str,
                       timecode: str):
        if timecode:
            start = timecode.split(' ')[0]
            return video_link + '&t=' + start + 's'
        return video_link

    def search(self,
               query: str) -> HTMLsentence:
        query_info = self.create_query_info(query)
        matching_sents = self.select_sentences([t.lemma for t in query_info.tokens])
        self.create_html_sentences(matching_sents)
        ...

