import sqlite3
from typing import List, Tuple, Optional
from contextlib import closing

from ..model import Sentence, Token


class TranscriptRepository:
    def __init__(self,
                 db_path: str,
                 db_conn: Optional[sqlite3.Connection] = None):
        self.db_path = db_path
        self.conn = db_conn

    def connect(self):
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path)

    def close(self):
        if self.conn is not None:
            self.conn.close()
            self.conn = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def create_tables(self,
                      foreign_key_tables: bool = False):
        self.connect()
        cursor = self.conn.cursor()

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS texts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            filename TEXT,
            youtube_link TEXT,
            timecode_start TEXT,
            timecode_end TEXT,
            math_branch_id INTEGER,
            level_id INTEGER
        )''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text_id INTEGER,
            sent TEXT,
            lemmatized TEXT,
            pos_in_text INTEGER,
            timecode TEXT,
            FOREIGN KEY (text_id) REFERENCES texts (id)
                ON DELETE CASCADE ON UPDATE CASCADE
        )''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS lemmas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE
        )''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS pos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            descr_rus TEXT,
            descr_eng TEXT,
            examples TEXT,
            UD_link TEXT UNIQUE
        )''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sent_id INTEGER,
            pos_in_sent INTEGER,
            token TEXT,
            whitespace BOOLEAN,
            lemma_id INTEGER,
            pos_id INTEGER,
            char_start INTEGER,
            char_end INTEGER,
            FOREIGN KEY (sent_id) REFERENCES sents (id)
                ON DELETE CASCADE ON UPDATE CASCADE,
            FOREIGN KEY (lemma_id) REFERENCES lemmas (id)
                ON UPDATE CASCADE ON DELETE SET NULL,
            FOREIGN KEY (pos_id) REFERENCES pos (id)
                ON UPDATE CASCADE ON DELETE SET NULL
        )''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS morph_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE
        )''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS morph_values (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE
        )''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS morph_features (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token_id INTEGER,
            category_id INTEGER,
            value_id INTEGER,
            FOREIGN KEY (token_id) REFERENCES tokens (id)
                ON DELETE CASCADE ON UPDATE CASCADE,
            FOREIGN KEY (category_id) REFERENCES morph_categories (id)
                ON DELETE SET NULL ON UPDATE CASCADE,
            FOREIGN KEY (value_id) REFERENCES morph_values (id)
                ON DELETE SET NULL ON UPDATE CASCADE,
            UNIQUE (token_id, category_id)
        )''')

        self.conn.commit()


    def _add_sentence(self,
                      sentence: Sentence):
        cur = self.conn.execute(
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
                      lemma: str) -> int:
        cur = self.conn.execute('''SELECT id
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
                    pos: str) -> int:
        cur = self.conn.execute('''SELECT id
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
                               category: str) -> int:
        cur = self.conn.execute('''SELECT id
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
                            value: str) -> int:
        cur = self.conn.execute('''SELECT id
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
                        token_id: int,
                        morph_info: str):
        for morph in morph_info.split('|'):
            category, value = morph.split('=')
            category_id = self._get_morph_category_id(category)
            value_id = self._get_morph_value_id(value)
            self.conn.execute('''
            INSERT INTO morph_features (token_id, category_id, value_id) 
            VALUES (?, ?, ?)''', (token_id, category_id, value_id))

    def _add_token(self,
                   token: Token):
        lemma_id = self._get_lemma_id(token.lemma)
        pos_id = self._get_pos_id(token.pos_tag)
        cur = self.conn.execute('''
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
        self._add_morph_info(token_id, token.morph_annotation)

    def add_transcript(self, sentences: List[Sentence]):
        self.connect()
        with self.conn:
            for sentence in sentences:
                sent_id = self._add_sentence(sentence)
                for token in sentence.tokens:
                    token.sentence_id = sent_id
                    self._add_token(token)

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


if __name__ == '__main__':
    db_path = ':memory:'
    conn = sqlite3.connect(db_path)
    lecture_repo = TranscriptRepository(db_path, conn)

    lecture_repo.create_tables()
    cur = conn.execute('''SELECT name FROM sqlite_master WHERE type='table';''')
    print(cur.fetchall())