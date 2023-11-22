from typing import Iterable, Dict, Union, Tuple
import re

from spacy import Language

from .html_models import HTMLSpan, HTMLWord, HTMLsentence, QueryInfo
from .database import WebDBHandler


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

    def token_within_query(self,
                           query_lemmatized: Iterable[str],
                           sentence_lemmatized: Iterable[str],
                           token_idx: int):
        i_token_char_start = len(' '.join(sentence_lemmatized[: token_idx])) + 1
        i_token_char_end = i_token_char_start + len(sentence_lemmatized[token_idx])
        reg_ex = r"\s?([А-Яа-яёЁ]+)?\s?".join(query_lemmatized)  # можно одно слово между не из запроса
        reg_ex = r"((?<=^)|(?<=\s))" + reg_ex + r"(?=$|\s)"  # чтобы не находились в середине слова

        for m in re.finditer(reg_ex, ' '.join(sentence_lemmatized)):
            if i_token_char_start >= m.start() and i_token_char_end <= m.end():
                return True
        return False

    def user_favourites(self,
                        userid: int):
        ...

    def create_html_sentences(self,
                              userid: int,
                              query_info: QueryInfo,
                              selected_sents) -> Iterable[HTMLsentence]:
        html_sentences = []
        if userid:
            user_favs = self.db.get_user_favourites(userid)
        else:
            user_favs = []
        sorted_sents = sorted(selected_sents, key=lambda x: 1 if x[0] in user_favs else 0, reverse=True)
        query_lemmatized = [t.lemma for t in query_info.tokens]
        for sent_id, match in sorted_sents:
            html_sentence = HTMLsentence(sent_id)
            if sent_id in user_favs:
                html_sentence.star = True
            sent_info = self.db.sent_info(sent_id)
            left, right = self.db.sent_context(sent_info['text_id'], sent_info['pos_in_text'])
            html_sentence.left = left
            html_sentence.right = right
            html_sentence.yb_link = self.create_yb_link(sent_info['youtube_link'], sent_info['timecode'])

            tokens = self.db.sent_token_info(sent_id)
            sent_lemmatized = [t['lemma'] for t in tokens]
            i = 0
            for t in self.html_tokens_generator(tokens):
                if isinstance(t, HTMLWord) and self.token_within_query(query_lemmatized, sent_lemmatized, i):
                    # TODO: Переписать весь этот ужас с окрашиванием токенов
                    try:
                        token_idx_in_query = query_lemmatized.index(t.lemma)
                        t.color = query_info.tokens[token_idx_in_query].color
                    except ValueError:
                        t.color = 'black'
                html_sentence.tokens.append(t)
                if t.html_type == 'tooltip' or t.text.strip():
                    i += 1
            html_sentences.append(html_sentence)
        return html_sentences

    def color_result_word(self,
                          query_info: QueryInfo,
                          token_info: HTMLWord,
                          sentence_match_spans: Iterable[Tuple[int, int]]):
        query_lemmas = [t.lemma for t in query_info.tokens]
        try:
            token_idx_in_query = query_lemmas.index(token_info.lemma)
            print('token index in query', token_idx_in_query)
            for span in sentence_match_spans:
                print(span)
                if token_info.char_start_ >= span[0] and token_info.char_end_ <= span[1]:
                    print('yes')
                    return query_info.tokens[token_idx_in_query].color
            return 'black'
        except ValueError:
            return 'black'


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
                               char_end_=token['char_end'])
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

