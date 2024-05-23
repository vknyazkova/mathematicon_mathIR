from typing import Tuple, List, Optional, Generator, Union

from spacy import Language

from ..services.lecture_transcript_service import LectureTranscriptService
from ..services.formula_annotation_service import FormulaAnnotationService
from ..models.html_models import HTMLWord, HTMLSentence, QueryInfo, HTMLSpan, HTMLAnnotated
from ..model import Sentence, Token, AnnotationFragment


class SearchService:
    def __init__(self,
                 nlp: Language,
                 lecture_transcript_service: LectureTranscriptService,
                 formula_service: FormulaAnnotationService):
        self.nlp = nlp
        self.lecture_transcript_service = lecture_transcript_service
        self.formula_service = formula_service

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

    @staticmethod
    def _html_tokens_generator(tokens: List[Token],
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
                               color=color)
            else:
                plain_token.text += token.token_text
            whitespace = ' ' if token.whitespace else ''
            plain_token.text += whitespace
        if plain_token.text:
            yield plain_token

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

    @staticmethod
    def _color_tokens(n_tokens: int,
                      query_info: QueryInfo,
                      matches: List[List[int]]) -> List[str]:
        # matches = [[qw1, qw2, qw3], [qw1, qw2, qw3]]
        token_colors = []
        mp = 0
        qp = 0
        for i in range(n_tokens):
            if i == matches[mp][qp]:
                token_colors.append(query_info.tokens[qp].color)
                qp += 1
                if qp == len(matches[mp]):
                    mp += 1
                    qp = 0
                    if mp == len(matches):
                        token_colors.extend(['black' for _ in range(i + 1, n_tokens)])
                        break
            else:
                token_colors.append('black')
        return token_colors

    def _create_html_sentence(self,
                              sentence: Sentence,
                              token_colors: List[str]) -> HTMLSentence:
        left_context, right_context = self.lecture_transcript_service.get_sentence_context(sentence)
        html_sentence = HTMLSentence(
            id=sentence.sentence_id,
            tokens=list(self._html_tokens_generator(sentence.tokens, token_colors)),
            left=left_context,
            right=right_context,
            yb_link=self.lecture_transcript_service.get_sentence_yb_link(sentence)
        )
        return html_sentence

    @staticmethod
    def generate_html_annotated_tokens(tokens: List[Token],
                                       annot_fragment: AnnotationFragment) -> List[Union[HTMLAnnotated, HTMLSpan]]:
        html_spans = []
        annotated_tokens = []
        non_annotated_tokens = []
        for token in tokens:
            if token.char_offset_end <= annot_fragment.char_end and token.char_offset_start >= annot_fragment.char_start:
                if len(non_annotated_tokens) > 0:
                    html_spans.extend(
                        list(SearchService._html_tokens_generator(non_annotated_tokens, ['black' for _ in non_annotated_tokens])))
                    non_annotated_tokens = []
                annotated_tokens.append(token)
            else:
                if len(annotated_tokens) > 0:
                    html_spans.append(
                        HTMLAnnotated(
                            annotation=annot_fragment.annotation.tex_formula,
                            spans=list(SearchService._html_tokens_generator(annotated_tokens, ['black' for _ in  annotated_tokens]))
                        )
                    )
                    annotated_tokens = []
                non_annotated_tokens.append(token)
        if len(non_annotated_tokens) > 0:
            html_spans.extend(
                list(SearchService._html_tokens_generator(non_annotated_tokens,
                                                          ['black' for _ in non_annotated_tokens])))
        elif len(annotated_tokens) > 0:
            html_spans.append(
                HTMLAnnotated(
                    annotation=annot_fragment.annotation.tex_formula,
                    spans=list(
                        SearchService._html_tokens_generator(annotated_tokens, ['black' for _ in annotated_tokens]))
                )
            )
        return html_spans

    def _create_html_sentence_with_annotation(self,
                                              sentence: Sentence,
                                              annot_fragment: AnnotationFragment) -> HTMLSentence:
        html_spans = self.generate_html_annotated_tokens(sentence.tokens, annot_fragment)
        left_context, right_context = self.lecture_transcript_service.get_sentence_context(sentence)
        return HTMLSentence(
            id=sentence.sentence_id,
            tokens=html_spans,
            left=left_context,
            right=right_context,
            yb_link=self.lecture_transcript_service.get_sentence_yb_link(sentence),
        )


    def _construct_search_result(self,
                                 query_info: QueryInfo,
                                 found_sents: List[Sentence],
                                 by_lemma: bool = True) -> List[HTMLSentence]:
        html_sentences = []
        for sent in found_sents:
            matches = self._match_query_in_sentence(sent, query_info, by_lemma)
            if matches:
                tokens_color = self._color_tokens(n_tokens=len(sent.tokens),
                                                  query_info=query_info,
                                                  matches=matches)
                html_sentences.append(self._create_html_sentence(sent, tokens_color))
        return html_sentences

    def exactMatchSearch(self,
                           query: str) -> Tuple[QueryInfo, List[HTMLSentence]]:
        query_info = self._create_query_info(query)
        found_sents = self.lecture_transcript_service.exact_match_search(query)
        search_result = self._construct_search_result(query_info, found_sents, by_lemma=False)
        return query_info, search_result

    def lemmaSearch(self,
                    query: str) -> Tuple[QueryInfo, List[HTMLSentence]]:
        query_info = self._create_query_info(query)
        query_match_pattern = [t.lemma for t in query_info.tokens]
        found_sents = self.lecture_transcript_service.lemmatized_search(query_match_pattern)
        search_result = self._construct_search_result(query_info, found_sents, by_lemma=True)
        return query_info, search_result

    def searchByFormula(self,
                        tex_formula: str) -> Tuple[QueryInfo, List[HTMLSentence]]:
        # formula_fragments = self.formula_service.search_similar_formulas(tex_formula)
        # sentences = {}
        # html_sentences = []
        # for frag in formula_fragments:
        #     if frag.sentence_id not in sentences:
        #         sentences[frag.sentence_id] = self.lecture_transcript_service.get_sentence_by_id(frag.sentence_id)
        ...


