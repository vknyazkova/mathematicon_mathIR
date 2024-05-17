import re
from typing import Tuple, List, Optional, Generator

from spacy import Language

from ..repositories.transcript_repo import TranscriptRepository
from ..models.html_models import HTMLWord, HTMLSentence, QueryInfo, HTMLSpan
from ..model import Sentence, Token


class TextSearchService:
    def __init__(self,
                 nlp: Language,
                 transcript_repo: TranscriptRepository):
        self.transcript_repo = transcript_repo
        self.nlp = nlp

    @staticmethod
    def find_pattern_in_target(pattern: List[str],
                               target: List[str],
                               max_skips: int = 0) -> Optional[List[List[int]]]:
        p = 0  # pattern pointer
        skips = 0  # counter of skips between two matched elements
        matches = []
        match_ = []
        for i in range(len(target)):
            if pattern[p] == target[i]:  # elements matched
                if skips <= max_skips:
                    if p == len(pattern) - 1:  # full match
                        match_.append(i)
                        matches.append(match_)
                        # start new match
                        match_ = []
                        p = 0
                        skips = 0
                    else:  # partial match
                        match_.append(i)
                        p += 1
                else:  # too many skips
                    # start new match
                    match_ = []
                    p = 0
                    skips = 0
            else:  # non matching elements
                if match_:  # if match is started increase skips
                    skips += 1
        if matches:
            return matches
        return None

    def _create_query_info(self,
                           query: str) -> QueryInfo:
        query_info = QueryInfo()
        for t in self.nlp(query):
            token = HTMLWord(text=t.text,
                             html_type='plain',
                             pos=t.pos_,
                             lemma=t.lemma_,
                             color='green')
            query_info.tokens.append(token)
        return query_info

    def _html_tokens_generator(self,
                               tokens: List[Token],
                               colors: List[str]) -> Generator[HTMLSpan, None, None]:
        """
        Generates HTML tokens based on token information.

        Args:
            tokens (Iterable[dict]): Iterable of token information.

        Yields:
            HTMLSpan or HTMLWord: HTMLSpan for punctuation tokens and HTMLWord for other tokens.
        """
        plain_token = HTMLSpan('')
        for token, color in zip(tokens, colors):
            if not token.pos_tag == 'PUNCT':
                if plain_token.text:
                    yield plain_token
                    plain_token = HTMLSpan('')
                yield HTMLWord(text=token.token_text,
                               pos=token.pos_tag,
                               lemma=token.lemma,
                               char_start_=token.char_offset_start,
                               char_end_=token.char_offset_end,
                               color=color)
            else:
                plain_token.text += token.token_text
            whitespace = ' ' if token.whitespace else ''
            plain_token.text += whitespace

    def _match_query_in_sentence(self,
                                 sentence: Sentence,
                                 query_info: QueryInfo,
                                 by_lemma: bool = True) -> Optional[List[List[int]]]:
        if by_lemma:
            pattern = [t.lemma for t in query_info.tokens]
            target = [t.lemma for t in sentence.tokens]
            max_skips = 1
        else:
            pattern = [t.text for t in query_info.tokens]
            target = [t.token_text for t in sentence.tokens]
            max_skips = 0

        return self.find_pattern_in_target(pattern, target, max_skips)

    def _color_tokens(self,
                      tokens: List[Token],
                      query_info: QueryInfo,
                      matches: List[List[int]]) -> List[str]:
        token_colors = []
        mp = 0
        qp = 0
        for i, token in enumerate(tokens):
            if i in matches[mp][qp]:
                token_colors.append(query_info.tokens[qp])
                qp += 1
                if qp == len(matches[mp]):
                    mp += 1
                    qp = 0
                    if mp == len(matches[mp]):
                        token_colors.extend(['black' for _ in range(i + 1, len(tokens))])
                        break
        return token_colors

    def _create_html_sentence(self,
                              sentence: Sentence,
                              token_colors: List[str]) -> HTMLSentence:
        left_context, right_context = self.transcript_repo.sentence_context(sentence)
        html_sentence = HTMLSentence(
            id=sentence.sentence_id,
            tokens=list(self._html_tokens_generator(sentence.tokens, token_colors)),
            left=left_context.sentence_text,
            right=right_context.sentence_text,
            yb_link=self.transcript_repo.get_sentence_yb_link(sentence)
        )
        return html_sentence

    def search_text(self, query: str) -> Tuple[QueryInfo, List[HTMLSentence]]:
        # exact match search
        if re.match(r'".*"', query):
            query = query[1:-1]
            query_info = self._create_query_info(query)
            found_sents = self.transcript_repo.search_phrase(query)
            by_lemma = False

        # lemmatized search
        else:
            query_info = self._create_query_info(query)
            query_match_pattern = [t.lemma for t in query_info.tokens]
            found_sents = self.transcript_repo.search_lemmatized(query_match_pattern)
            by_lemma = False

        html_sentences = []
        for sent in found_sents:
            matches = self._match_query_in_sentence(sent, query_info, by_lemma)
            if matches:
                tokens_color = self._color_tokens(tokens=sent.tokens,
                                                  query_info=query_info,
                                                  matches=matches)
                html_sentences.append(self._create_html_sentence(sent, tokens_color))
        return query_info, html_sentences


