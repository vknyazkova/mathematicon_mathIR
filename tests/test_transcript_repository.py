import unittest
import sqlite3

from mathematicon.backend.repositories.transcript_repo import TranscriptRepository
from mathematicon.backend.model import Sentence, Token


class TestTranscriptRepository(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(':memory:')
        self.repo = TranscriptRepository(db_path=':memory:', db_conn=self.conn)
        self.repo.create_tables()

    def tearDown(self):
        self.conn.close()

    def test_add_transcript(self):
        transcript = [
            Sentence(
                lecture_id=1,
                position_in_text=1,
                sentence_text='Запишите уравнение.',
                lemmatized_sentence='записать уравнение .',
                timecode_start='0',
                tokens=[
                    Token(token_text='Запишите', whitespace=True, pos_tag='VERB', lemma='записать',
                          morph_annotation='Aspect=Perf|Mood=Imp|Number=Plur|Person=Second|VerbForm=Fin|Voice=Act',
                          position_in_sentence=0, char_offset_start=0, char_offset_end=8),
                    Token(token_text='уравнение', whitespace=False, pos_tag='NOUN', lemma='уравнение',
                          morph_annotation='Animacy=Inan|Case=Acc|Gender=Neut|Number=Sing', position_in_sentence=1,
                          char_offset_start=9, char_offset_end=18),
                    Token(token_text='.', whitespace=True, pos_tag='PUNCT', lemma='.', morph_annotation='',
                          position_in_sentence=2, char_offset_start=18, char_offset_end=19)
                ]
            ),
            Sentence(
                lecture_id=1,
                position_in_text=2,
                sentence_text='Запишите уравнение.',
                lemmatized_sentence='записать уравнение .',
                timecode_start='2',
                tokens=[
                    Token(token_text='Два', whitespace=True, pos_tag='NUM', lemma='два',
                          morph_annotation='Case=Nom|Gender=Masc', position_in_sentence=0, char_offset_start=0,
                          char_offset_end=3),
                    Token(token_text='деленное', whitespace=True, pos_tag='VERB', lemma='деленное',
                          morph_annotation='Aspect=Perf|Case=Nom|Gender=Neut|Number=Sing|Tense=Past|VerbForm=Part|Voice=Pass',
                          position_in_sentence=1, char_offset_start=4, char_offset_end=12),
                    Token(token_text='на', whitespace=True, pos_tag='ADP', lemma='на', morph_annotation='',
                          position_in_sentence=2, char_offset_start=13, char_offset_end=15),
                    Token(token_text='икс', whitespace=True, pos_tag='NOUN', lemma='икс',
                          morph_annotation='Animacy=Inan|Case=Acc|Gender=Masc|Number=Sing', position_in_sentence=3,
                          char_offset_start=16, char_offset_end=19),
                    Token(token_text='плюс', whitespace=True, pos_tag='ADP', lemma='плюс', morph_annotation='',
                          position_in_sentence=4, char_offset_start=20, char_offset_end=24),
                    Token(token_text='два', whitespace=False, pos_tag='NUM', lemma='два',
                          morph_annotation='Animacy=Inan|Case=Acc|Gender=Masc', position_in_sentence=5,
                          char_offset_start=25, char_offset_end=28),
                    Token(token_text='.', whitespace=False, pos_tag='PUNCT', lemma='.', morph_annotation='',
                          position_in_sentence=6, char_offset_start=28, char_offset_end=29)
                ]
            )
        ]

        sentences = self.repo.add_transcript(transcript)

        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM sents")
        sents_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM tokens")
        tokens_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM pos")
        pos_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM lemmas")
        lemma_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM morph_categories")
        mc_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM morph_values")
        mv_count = cur.fetchone()[0]

        self.assertEqual(sents_count, 2, "There should be 2 sentences.")
        self.assertEqual(tokens_count, 10, "There should be 10 tokens.")
        self.assertEqual(pos_count, 5, "There should be 5 unique pos tags.")
        self.assertEqual(lemma_count, 8, "There should be 8 unique lemma tags.")
        self.assertEqual(mc_count, 10, "There should be 10 unique morph categories.")
        self.assertEqual(mv_count, 15, "There should be 15 unique morph values.")

