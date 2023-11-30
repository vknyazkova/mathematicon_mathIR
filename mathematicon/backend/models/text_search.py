from typing import Iterable, Tuple, Dict
import re
from bisect import bisect_left
from dataclasses import dataclass

from spacy import Language

from .html_models import HTMLSpan, HTMLWord, HTMLsentence, QueryInfo
from .database import WebDBHandler


@dataclass
class SentenceMatch:
    sent_id: int
    matches: Iterable[Tuple[int, int]]


class TextSearch:
    def __init__(self,
                 db: WebDBHandler,
                 nlp: Language):
        self.db = db
        self.nlp = nlp

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
        return 'green'

    def select_sentences(self,
                         lemmatized_query: Iterable[str]) -> Iterable[SentenceMatch]:
        similar_sents = self.db.get_sent_by_lemmatized_query(lemmatized_query)
        reg_ex = r"\s?([А-Яа-яёЁ]+)?\s?".join(lemmatized_query)  # можно одно слово между не из запроса
        reg_ex = r"((?<=^)|(?<=\s))" + reg_ex + r"(?=$|\s)"  # чтобы не находились в середине слова
        matching_sents = []
        for sent in similar_sents:
            matches = [m.span() for m in re.finditer(reg_ex, sent['lemmatized'])]
            if matches:
                matching_sents.append(SentenceMatch(
                    sent_id=sent['id'],
                    matches=matches
                ))
        return matching_sents

    def tokens_inside_matches(self,
                              lemmatized_sent: str,
                              query_match_spans: Iterable[Tuple[int, int]]):
        lemmas_char_starts = [
            match.start() for match in re.finditer(r"\S+", lemmatized_sent)
        ]
        match_tokens_id = []
        for span in query_match_spans:
            token_start = bisect_left(lemmas_char_starts, span[0])
            token_end = bisect_left(lemmas_char_starts, span[1])
            match_tokens_id.extend(range(token_start, token_end))
        return match_tokens_id

    def sort_sents_by_favourites(self,
                                 userid: int,
                                 selected_sents: Iterable[SentenceMatch]) -> Tuple[Iterable[int], Iterable[SentenceMatch]]:
        if userid:
            user_favs = self.db.get_user_favourites(userid)
            sorted_sents = sorted(
                selected_sents, key=lambda x: 1 if x.sent_id in user_favs else 0, reverse=True
            )
        else:
            user_favs = []
            sorted_sents = selected_sents
        return user_favs, sorted_sents


    def color_sentence_tokens(self,
                              matched_sent: SentenceMatch,
                              query: QueryInfo):

        tokens = self.db.sent_token_info(matched_sent.sent_id)
        sent_lemmatized = ' '.join(t["lemma"] for t in tokens)

        query_lemmas = [w.lemma for w in query.tokens]
        query_colors = [w.color for w in query.tokens]
        query_tokens = self.tokens_inside_matches(sent_lemmatized, matched_sent.matches)

        colored_tokens = []
        for i, t in enumerate(tokens):
            if i in query_tokens:
                try:
                    query_lemma_idx = query_lemmas.index(t['lemma'])
                    t['color'] = query_colors[query_lemma_idx]
                except ValueError:
                    t['color'] = 'black'
            else:
                t["color"] = "black"
            colored_tokens.append(t)
        return colored_tokens

    def create_html_sentences(self,
                             userid: int,
                             query_info: QueryInfo,
                             selected_sents: Iterable[SentenceMatch]) -> Iterable[HTMLsentence]:
        html_sentences = []
        user_favs, selected_sents = self.sort_sents_by_favourites(userid, selected_sents)
        for sent in selected_sents:
            sent_info = self.db.sent_info(sent.sent_id)
            left, right = self.db.sent_context(sent_info["text_id"], sent_info["pos_in_text"])
            html_sentence = HTMLsentence(
                id=sent.sent_id,
                left=left,
                right=right,
                yb_link=self.create_yb_link(sent_info['youtube_link'], sent_info['timecode']),
                star="true" if sent.sent_id in user_favs else "false"
            )
            tokens_info = self.color_sentence_tokens(sent, query_info)
            for html_token in self.html_tokens_generator(tokens_info):
                html_sentence.tokens.append(html_token)
            html_sentences.append(html_sentence)
        return html_sentences

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
                               lemma=token['lemma'],
                               char_start_=token['char_start'],
                               char_end_=token['char_end'],
                               color=token['color'])
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
               query: str,
               userid: int,
               search_type: str = 'lemma') -> Tuple[QueryInfo, Iterable[HTMLsentence]]:
        query_info = self.create_query_info(query)
        if search_type == 'lemma':
            matching_sents = self.select_sentences([t.lemma for t in query_info.tokens])
            results = self.create_html_sentences(userid, query_info, matching_sents)
        else:
            raise NotImplementedError
        return query_info, results

