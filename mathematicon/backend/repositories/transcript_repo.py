import sqlite3
from typing import List, Tuple, Optional
from contextlib import closing

from ..model import Sentence, Token


class TranscriptRepository:
    def __init__(self, db_path):
        self.db_path = db_path

    def _add_sentence(self,
                      conn: sqlite3.Connection,
                      sentence: Sentence):
        cur = conn.execute(
            '''
            INSERT INTO sents (text_id, sent, lemmatized, pos_in_text)
            VALUES (?, ?, ?, ?)
            RETURNING id
            ''',
            (sentence.lecture_id,
             sentence.sentence_text,
             sentence.lemmatized_sentence,
             sentence.position_in_text)
        )
        return cur.fetchone()[0]

    def _get_lemma_id(self,
                      conn: sqlite3.Connection,
                      lemma: str) -> int:
        cur = conn.execute('''SELECT id
        FROM lemmas
        WHERE name = (?)''', (lemma, ))
        id_ = cur.fetchone()
        if not id_:
            cur.execute('''
                    INSERT INTO lemmas (name)
                    VALUES (?)
                    RETURNING id''', (lemma,))
            id_ = cur.fetchone()
        return id_[0]

    def _get_pos_id(self,
                    conn: sqlite3.Connection,
                    pos: str) -> int:
        cur = conn.execute('''SELECT id
                FROM pos
                WHERE name = (?)''', (pos,))
        id_ = cur.fetchone()
        if not id_:
            cur.execute('''
                        INSERT INTO pos (name)
                        VALUES (?)
                        RETURNING id''', (pos,))
            id_ = cur.fetchone()
        return id_[0]

    def _get_morph_category_id(self,
                               conn: sqlite3.Connection,
                               category: str) -> int:
        cur = conn.execute('''SELECT id
                        FROM morph_categories
                        WHERE name = (?)''', (category,))
        id_ = cur.fetchone()
        if not id_:
            cur.execute('''
                        INSERT INTO morph_categories (name)
                        VALUES (?)
                        RETURNING id''', (category,))
            id_ = cur.fetchone()
        return id_[0]

    def _get_morph_value_id(self,
                            conn: sqlite3.Connection,
                            value: str) -> int:
        cur = conn.execute('''SELECT id
                        FROM morph_values
                        WHERE name = (?)''', (value,))
        id_ = cur.fetchone()
        if not id_:
            cur.execute('''
                        INSERT INTO morph_values (name)
                        VALUES (?)
                        RETURNING id''', (value,))
            id_ = cur.fetchone()
        return id_[0]

    def _add_morph_info(self,
                        conn: sqlite3.Connection,
                        token_id: int,
                        morph_info: str):
        for morph in morph_info.split('|'):
            category, value = morph.split('=')
            category_id = self._get_morph_category_id(conn, category)
            value_id = self._get_morph_value_id(conn, value)
            conn.execute('''
            INSERT INTO morph_features (token_id, category_id, value_id) 
            VALUES (?, ?, ?)''', (token_id, category_id, value_id))

    def _add_token(self,
                   conn: sqlite3.Connection,
                   token: Token):
        lemma_id = self._get_lemma_id(conn, token.lemma)
        pos_id = self._get_pos_id(conn, token.pos_tag)
        cur = conn.execute('''
        INSERT INTO tokens (sent_id, pos_in_sent, token, whitespace, char_start, char_end, lemma_id, pos_id) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        RETURNING id''', (
            token.sentence_id,
            token.position_in_sentence,
            token.token_text,
            token.whitespace,
            token.char_offset_start,
            token.char_offset_end,
            lemma_id,
            pos_id
        ))
        token_id = cur.fetchone()[0]
        self._add_morph_info(conn, token_id, token.morph_annotation)

    def add_transcript(self, sentences: List[Sentence]):
        with closing(sqlite3.connect(self.db_path)) as conn:
            for sentence in sentences:
                sent_id = self._add_sentence(conn, sentence)
                for token in sentence.tokens:
                    token.sentence_id = sent_id
                    self._add_token(conn, token)
        conn.close()

    def search_lemmatized(self, lemmatized_query: List[str]) -> List[Sentence]:
        ...

    def search_phrase(self, phrase: str) -> List[Sentence]:
        ...

    def sentence_context(self, sentence: Sentence) -> Tuple[Optional[Sentence], Optional[Sentence]]:
        text_id = sentence.lecture_id
        pos_in_text = sentence.position_in_text
        with closing(sqlite3.connect(self.db_path)) as conn:
            cur = conn.execute('''
            SELECT sents.sent
            FROM sents
            WHERE text_id = :text_id
            AND (pos_in_text = :pos_in_text - 1)
            ''', {'text_id': text_id, 'pos_in_text': pos_in_text})
            cur.row_factory = self.one_column_factory
            left = cur.fetchone()
            cur = self.conn.execute(
                """
                    SELECT sents.sent
                    FROM sents
                    WHERE text_id = :text_id
                    AND (pos_in_text = :pos_in_text + 1)
                    """,
                {"text_id": text_id, "pos_in_text": pos_in_text},
            )
            cur.row_factory = self.one_column_factory
            right = cur.fetchone()
        return left, right

    def get_sentence_yb_link(self, sentence: Sentence) -> str:
        ...