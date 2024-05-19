from typing import Tuple, List, Optional, Generator

from spacy import Language

from ..repositories.transcript_repo import TranscriptRepository
from ..repositories.lecture_repo import LectureRepository
from ..models.html_models import HTMLWord, HTMLSentence, QueryInfo, HTMLSpan
from ..model import Sentence, Token


class SearchService:
    def __init__(self,
                 nlp: Language,
                 lecture_repo: LectureRepository,
                 transcript_repo: TranscriptRepository):
        self.lecture_repo = lecture_repo
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
        # matches = [[qw1, qw2, qw3], [qw1, qw2, qw3]]
        token_colors = []
        mp = 0
        qp = 0
        for i, token in enumerate(tokens):
            if i == matches[mp][qp]:
                token_colors.append(query_info.tokens[qp])
                qp += 1
                if qp == len(matches[mp]):
                    mp += 1
                    qp = 0
                    if mp == len(matches):
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
            left=left_context,
            right=right_context,
            yb_link=self.transcript_repo.get_sentence_yb_link(sentence)
        )
        return html_sentence

    def _construct_search_result(self,
                                 query_info: QueryInfo,
                                 found_sents: List[Sentence],
                                 by_lemma: bool = True) -> List[HTMLSentence]:
        html_sentences = []
        for sent in found_sents:
            matches = self._match_query_in_sentence(sent, query_info, by_lemma)
            if matches:
                tokens_color = self._color_tokens(tokens=sent.tokens,
                                                  query_info=query_info,
                                                  matches=matches)
                html_sentences.append(self._create_html_sentence(sent, tokens_color))
        return html_sentences

    def exactMatchSearch(self,
                           query: str) -> Tuple[QueryInfo, List[HTMLSentence]]:
        query_info = self._create_query_info(query)
        found_sents = self.transcript_repo.search_phrase(query)
        return query_info, self._construct_search_result(query_info, found_sents, by_lemma=False)

    def lemmaSearch(self,
                    query: str) -> Tuple[QueryInfo, List[HTMLSentence]]:
        query_info = self._create_query_info(query)
        query_match_pattern = [t.lemma for t in query_info.tokens]
        found_sents = self.transcript_repo.search_lemmatized(query_match_pattern)
        return query_info, self._construct_search_result(query_info, found_sents, by_lemma=True)

    def searchByFormula(self,
                        tex_formula: str) -> Tuple[QueryInfo, List[HTMLSentence]]:
        ...


if __name__ == '__main__':
    import sqlite3
    import spacy
    from spacy.language import Language

    from mathematicon.backend.model import MathLecture, Sentence
    from mathematicon.backend.models.mathematicon_morph_parser import MorphologyCorrectionHandler

    @Language.factory(
        "morphology_corrector",
        assigns=["token.lemma", "token.tag"],
        requires=["token.pos"],
        default_config={"mode": "ptcp+conv"},
    )
    def morphology_corrector(nlp, name, mode):
        return MorphologyCorrectionHandler(mode=mode)


    nlp = spacy.load("ru_core_news_sm", exclude=["ner"])
    nlp.add_pipe('morphology_corrector', after='lemmatizer')


    db_path = ':memory:'
    conn = sqlite3.connect(db_path)
    lecture_repo = LectureRepository(db_path, conn)
    lecture_repo.create_tables()
    transcript_repo = TranscriptRepository(db_path, conn)
    transcript_repo.create_tables()

    lecture1 = MathLecture(
        title="Sample Lecture",
        filename="sample.mp4",
        youtube_link="https://youtube.com/sample",
        timecode_start="0",
        timecode_end="60",
        math_branch="Algebra",
        difficulty_level="Intermediate"
    )

    lecture1 = lecture_repo.add_lecture(lecture1)

    transcript = [
        Sentence(
            lecture_id=lecture1.lecture_id,
            position_in_text=1,
            sentence_text='Запишите уравнение.',
            lemmatized_sentence='записать уравнение .',
            timecode_start='00:00',
            tokens=[
                Token(token_text='Запишите', whitespace=True, pos_tag='VERB', lemma='записать',
                      morph_annotation='Aspect=Perf|Mood=Imp|Number=Plur|Person=Second|VerbForm=Fin|Voice=Act',
                      position_in_sentence=1, char_offset_start=0, char_offset_end=8),
                Token(token_text='уравнение', whitespace=False, pos_tag='NOUN', lemma='уравнение',
                      morph_annotation='Animacy=Inan|Case=Acc|Gender=Neut|Number=Sing',
                      position_in_sentence=1, char_offset_start=9, char_offset_end=17),
                Token(token_text='.', whitespace=True, pos_tag='PUNCT', lemma='.', morph_annotation='',
                      position_in_sentence=1, char_offset_start=18, char_offset_end=19),
            ]
        ),
        Sentence(
            lecture_id=1,
            position_in_text=2,
            sentence_text='Два деленное на икс',
            lemmatized_sentence='два делённый|делить на икс .',
            timecode_start='00:00',
            tokens=[
                Token(token_text='Двa', whitespace=True, pos_tag='NUM', lemma='два',
                      morph_annotation='Case=Nom|Gender=Masc',
                      position_in_sentence=1, char_offset_start=0, char_offset_end=2),
                Token(token_text='деленное', whitespace=True, pos_tag='PTCP|VERB', lemma='делённый|делить',
                      morph_annotation='Aspect=Perf|Case=Nom|Gender=Neut|Number=Sing|Tense=Past|VerbForm=Part|Voice=Pass',
                      position_in_sentence=1, char_offset_start=0, char_offset_end=2),
                Token(token_text='на', whitespace=True, pos_tag='ADP', lemma='на', morph_annotation='',
                      position_in_sentence=1, char_offset_start=0, char_offset_end=2),
                Token(token_text='икс', whitespace=False, pos_tag='NOUN', lemma='икс',
                      morph_annotation='Animacy=Inan|Case=Acc|Gender=Masc|Number=Sing',
                      position_in_sentence=1, char_offset_start=0, char_offset_end=2),
                Token(token_text='.', whitespace=False, pos_tag='PUNCT', lemma='.', morph_annotation='',
                      position_in_sentence=1, char_offset_start=0, char_offset_end=2),
            ]
        ),
    ]
    sentences = transcript_repo.add_transcript(transcript)

    search_service = SearchService(nlp, lecture_repo, transcript_repo)
    print(search_service.lemmaSearch('записать уравнения'))
    conn.close()
