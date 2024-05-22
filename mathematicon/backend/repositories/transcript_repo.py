import sqlite3
from typing import List, Tuple, Optional

from ..model import Sentence, Token


class TranscriptRepository:

    def __init__(self,
                 db_path: str,
                 db_conn: Optional[sqlite3.Connection] = None):
        self.db_path = db_path
        self.conn = db_conn

    @staticmethod
    def sentence_mapper_factory(cursor: sqlite3.Cursor,
                                row) -> Sentence:
        fields = [column[0] for column in cursor.description]
        attrs = {key: value for key, value in zip(fields, row)}
        return Sentence(**attrs)

    @staticmethod
    def token_mapper_factory(cursor: sqlite3.Cursor,
                             row) -> Token:
        fields = [column[0] for column in cursor.description]
        attrs = {key: value for key, value in zip(fields, row)}
        return Token(**attrs)

    def connect(self):
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=True)

    def close(self):
        if self.conn is not None:
            self.conn.close()
            self.conn = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def create_tables(self):
        self.connect()
        cursor = self.conn.cursor()

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
                   token: Token) -> Token:
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
        token.token_id = cur.fetchone()[0]
        if token.morph_annotation:
            self._add_morph_info(token.token_id, token.morph_annotation)
        return token

    def add_transcript(self, sentences: List[Sentence]) -> List[Sentence]:
        self.connect()
        with self.conn:
            for i in range(len(sentences)):
                sentences[i].sentence_id = self._add_sentence(sentences[i])
                for j in range(len(sentences[i].tokens)):
                    sentences[i].tokens[j].sentence_id = sentences[i].sentence_id
                    sentences[i].tokens[j] = self._add_token(sentences[i].tokens[j])
        return sentences

    def _fetch_tokens_info(self,
                           sentence: Sentence) -> Sentence:
        self.connect()
        cur = self.conn.execute('''
        SELECT
            tokens.id AS token_id,
            tokens.sent_id AS sentence_id,
            tokens.pos_in_sent AS position_in_sentence,
            tokens.token AS token_text,
            tokens.whitespace AS whitespace,
            l.name AS lemma,
            p.name AS pos_tag,
            tokens.char_start AS char_offset_start,
            tokens.char_end AS char_offset_end
        FROM
            tokens
        JOIN lemmas l ON tokens.lemma_id = l.id
        JOIN pos p ON tokens.pos_id = p.id
        WHERE
            tokens.sent_id = ?
        ORDER BY
            tokens.pos_in_sent''', (sentence.sentence_id,))
        cur.row_factory = self.token_mapper_factory
        sentence.tokens = cur.fetchall()
        return sentence

    def search_lemmatized(self, lemmatized_query: List[str]) -> List[Sentence]:
        self.connect()
        pattern = '%' + '%'.join(lemmatized_query) + '%'
        cur = self.conn.execute('''
        SELECT 
            s.id as sentence_id,
            s.text_id as lecture_id,
            s.pos_in_text as position_in_text,
            s.sent as sentence_text,
            s.lemmatized as lemmatized_sentence,
            s.timecode as timecode_start
        FROM sents s
        WHERE s.lemmatized LIKE ?''', (pattern,))
        cur.row_factory = self.sentence_mapper_factory
        sentences = cur.fetchall()
        for i in range(len(sentences)):
            sentences[i] = self._fetch_tokens_info(sentences[i])
        return sentences

    def search_phrase(self, phrase: str) -> List[Sentence]:
        self.connect()
        pattern = '%' + phrase + '%'
        cur = self.conn.execute('''
                SELECT 
                    s.id as sentence_id,
                    s.text_id as lecture_id,
                    s.pos_in_text as position_in_text,
                    s.sent as sentence_text,
                    s.lemmatized as lemmatized_sentence,
                    s.timecode as timecode_start
                FROM sents s
                WHERE s.sent LIKE ?''', (pattern,))
        cur.row_factory = self.sentence_mapper_factory
        sentences = cur.fetchall()
        for i in range(len(sentences)):
            sentences[i] = self._fetch_tokens_info(sentences[i])
        return sentences

    def sentence_context(self, sentence: Sentence) -> Tuple[Optional[str], Optional[str]]:
        text_id = sentence.lecture_id
        pos_in_text = sentence.position_in_text

        self.connect()
        cur = self.conn.execute('''
        SELECT sents.sent, iif(sents.pos_in_text = :pos_in_text - 1, 0, 1)
        FROM sents
        WHERE text_id = :text_id
        AND pos_in_text = :pos_in_text - 1
        ''', {'text_id': text_id, 'pos_in_text': pos_in_text})

        context = cur.fetchall()
        context_sents = {}
        if context is not None:
            for s in context:
                if s[1] == 1:
                    context_sents['right'] = s[0]
                else:
                    context_sents['left'] = s[0]
        return context_sents.get('left', None), context_sents.get('right', None)

    def get_sentence_yb_link(self, sentence: Sentence) -> str:
        # TODO: maybe better move to search service, because info about youtube lecture should be handled in lecture_repo

        self.connect()
        cur = self.conn.execute('''
        SELECT t.youtube_link || '&t=' || IFNULL(sents.timecode, t.timecode_start) || 's'
        FROM sents
        LEFT JOIN texts t on sents.text_id = t.id
        WHERE sents.id = ?''', (sentence.sentence_id,))
        return cur.fetchone()[0]

    def get_sentence_by_id(self, sentence_id: int) -> Sentence:
        self.connect()
        cur = self.conn.execute(
            '''SELECT 
            s.id as sentence_id,
            s.text_id as lecture_id,
            s.pos_in_text as position_in_text,
            s.sent as sentence_text,
            s.lemmatized as lemmatized_sentence,
            s.timecode as timecode_start
            FROM sents s
            WHERE s.id = :sentence_id''', (sentence_id,)
        )
        cur.row_factory = self.sentence_mapper_factory
        return cur.fetchone()


