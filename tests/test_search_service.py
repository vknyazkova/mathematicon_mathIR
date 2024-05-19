import unittest

from spacy import Language

from mathematicon.backend.services.search_service import SearchService
from mathematicon.backend.repositories.mock_repos import MockLectureRepository, MockTranscriptRepository
from mathematicon.backend.models.html_models import QueryInfo, HTMLWord, HTMLSpan
from mathematicon.backend.model import Token


class MockLanguage(Language):
    ...


class TestSearchService(unittest.TestCase):
    def test_find_pattern_in_target(self):
        pattern1 = ['три']
        sent1 = ['модуль', 'числа', 'минус', 'три', 'равен', 'три']

        pattern2 = ['два', 'три']
        sent2 = ['два', 'три', 'мочь', 'принимать', 'значение', 'ноль', ',', 'один', ',', 'два', 'и', 'три']

        self.assertEqual([[3], [5]], SearchService.find_pattern_in_target(pattern1, sent1))
        self.assertEqual([[0, 1], [9, 11]], SearchService.find_pattern_in_target(pattern2, sent2, max_skips=1))
        self.assertEqual([[0, 1]], SearchService.find_pattern_in_target(pattern2, sent2, max_skips=0))

    def test__color_tokens(self):
        query_info = QueryInfo(
            tokens=[
                HTMLWord(text='два', color='green'),
                HTMLWord(text='три', color='green')
            ]
        )
        match = [[0, 1], [9, 11]]
        n_tokens = 12
        expected = [
            'green',  # два
            'green',  # три
            'black',  # мочь
            'black',  # принимать
            'black',  # значение
            'black',  # ноль
            'black',  # ,
            'black',  # один
            'black',  # ,
            'green',  # два
            'black',  # и
            'green',  # три
            ]

        search_service = SearchService(MockLanguage(), MockLectureRepository(), MockTranscriptRepository())
        self.assertEqual(expected, search_service._color_tokens(n_tokens, query_info, match))

    def test__html_tokens_generator(self):
        search_service = SearchService(MockLanguage(), MockLectureRepository(), MockTranscriptRepository())

        tokens = [
            Token(token_text='Соответственно', whitespace=False, pos_tag='ADV', lemma='Соответственно',
                  morph_annotation='Degree=Pos', position_in_sentence=0, char_offset_start=0, char_offset_end=14),
            Token(token_text=',', whitespace=True, pos_tag='PUNCT', lemma=',', morph_annotation='',
                  position_in_sentence=1, char_offset_start=14, char_offset_end=15),
            Token(token_text='здесь', whitespace=True, pos_tag='ADV', lemma='здесь', morph_annotation='Degree=Pos',
                  position_in_sentence=2, char_offset_start=16, char_offset_end=21),
            Token(token_text='значок', whitespace=True, pos_tag='NOUN', lemma='значок',
                  morph_annotation='Animacy=Inan|Case=Nom|Gender=Masc|Number=Sing', position_in_sentence=3,
                  char_offset_start=22, char_offset_end=28),
            Token(token_text='«', whitespace=False, pos_tag='PUNCT', lemma='"', morph_annotation='',
                  position_in_sentence=4, char_offset_start=29, char_offset_end=30),
            Token(token_text='плюс', whitespace=False, pos_tag='NOUN', lemma='плюс',
                  morph_annotation='Animacy=Inan|Case=Nom|Gender=Masc|Number=Sing', position_in_sentence=5,
                  char_offset_start=30, char_offset_end=34),
            Token(token_text='»', whitespace=False, pos_tag='PUNCT', lemma='"', morph_annotation='',
                  position_in_sentence=6, char_offset_start=34, char_offset_end=35),
            Token(token_text='.', whitespace=False, pos_tag='PUNCT', lemma='.', morph_annotation='',
                  position_in_sentence=7, char_offset_start=35, char_offset_end=36),
        ]
        colors = ['black', 'black', 'black', 'black', 'black', 'green', 'black', 'black']

        result = [
            HTMLWord(text='Соответственно', pos='ADV', lemma='Соответственно'),
            HTMLSpan(text=', '),
            HTMLWord(text='здесь', pos='ADV', lemma='здесь'),
            HTMLSpan(text=' '),
            HTMLWord(text='значок', pos='NOUN', lemma='значок'),
            HTMLSpan(text=' «'),
            HTMLWord(text='плюс', pos='NOUN', lemma='плюс', color='green'),
            HTMLSpan(text='».')
        ]

        generated_html_tokens = list(search_service._html_tokens_generator(tokens, colors))
        self.assertEqual(result, generated_html_tokens)

        tokens2 = [
            Token(token_text='Семь', whitespace=True, pos_tag='NUM', lemma='семь', morph_annotation='Case=Nom',
                  position_in_sentence=0, char_offset_start=0, char_offset_end=4),
            Token(token_text='на', whitespace=True, pos_tag='ADP', lemma='на', morph_annotation='',
                  position_in_sentence=1, char_offset_start=5, char_offset_end=7),
            Token(token_text='три', whitespace=False, pos_tag='NUM', lemma='три',
                  morph_annotation='Animacy=Inan|Case=Acc', position_in_sentence=2, char_offset_start=8,
                  char_offset_end=11),
            Token(token_text='.', whitespace=False, pos_tag='PUNCT', lemma='.', morph_annotation='',
                  position_in_sentence=3, char_offset_start=11, char_offset_end=12),
        ]
        colors2 = ['black', 'black', 'green', 'black']

        result2 = [
            HTMLWord(text='Семь', pos='NUM', lemma='семь'),
            HTMLSpan(text=' '),
            HTMLWord(text='на', pos='ADP', lemma='на'),
            HTMLSpan(text=' '),
            HTMLWord(text='три', pos='NUM', lemma='три', color='green'),
            HTMLSpan(text='.'),
        ]

        generated_html_tokens2 = list(search_service._html_tokens_generator(tokens2, colors2))
        self.assertEqual(result2, generated_html_tokens2)
