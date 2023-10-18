import sqlite3
from typing import Iterable, Tuple

from .custom_dataclasses import DatabaseToken, DatabaseSentence, DatabaseText


class DBHandler:
    conn = None

    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)

    def __del__(self):
        self.conn.close()

    @staticmethod
    def dict_factory(cursor: sqlite3.Cursor, row):
        fields = [column[0] for column in cursor.description]
        return {key: value for key, value in zip(fields, row)}


class UserDBHandler(DBHandler):

    def get_user_by_uname(self, username):
        cur = self.conn.execute('''
        SELECT * 
        FROM users
        WHERE username = (?)
        ''', (username,))
        cur.row_factory = self.dict_factory
        return cur.fetchone()

    def add_user(self, username, password, salt, email):
        self.conn.execute('''
        INSERT INTO users (username, password, salt, email)
        VALUES (?, ?, ?, ?)''', (username, password, salt, email))
        self.conn.commit()


class TextDBHandler(DBHandler):

    def add_math_branch(self, name: str, commit: bool = True):
        self.conn.execute('''
        INSERT or IGNORE INTO math_branches (name)
        VALUES (?)''', (name, ))
        if commit:
            self.conn.commit()

    def add_text_level(self, name, commit: bool = True):
        self.conn.execute('''
                    INSERT or IGNORE INTO text_difficulty (name)
                    VALUES (?)''', (name,))
        if commit:
            self.conn.commit()

    def add_text(self, text: DatabaseText):
        """
        Adds record about text to database or updates if filename exists
        Args:
            text_info: instance of DatabaseText class
        """
        text_info = text.dict_()
        try:
            self.add_math_branch(text_info['branch'], commit=False)
            self.add_text_level(text_info['level'], commit=False)

            self.conn.execute('''
            INSERT INTO texts (title, filename, youtube_link, level_id, math_branch_id)
            VALUES (
            :title, 
            :filename, 
            :yb_link, 
            (SELECT id FROM text_difficulty WHERE name = :level), 
            (SELECT id FROM math_branches WHERE name = :branch)
            )
            ON CONFLICT (filename)
            DO UPDATE SET
            title = :title,
            youtube_link = :yb_link,
            level_id = (SELECT id FROM text_difficulty WHERE name = :level),
            math_branch_id = (SELECT id FROM math_branches WHERE name = :branch)
            WHERE filename = :filename''', text_info)
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            print(e)

    def add_sentence(self, sentence: DatabaseSentence) -> int:
        """
        Adds information about sentence
        Args:
            sentence_info: instance of DatabaseSentence class
        Returns:

        """
        sentence_info = sentence.dict_()
        try:
            self.conn.execute('''
            INSERT INTO sents (text_id, sent, lemmatized, pos_in_text)
            VALUES (
            (SELECT id FROM texts WHERE filename = :filename), 
            :sent_text, 
            :lemmatized, 
            :pos_in_text)''', sentence_info)
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            print(e)

    def add_lemmas(self, lemmas: Iterable[Tuple[str, ]], commit: bool = True):
        self.conn.executemany('''
        INSERT or IGNORE INTO lemmas (name)
        VALUES (?)''', lemmas)
        if commit:
            self.conn.commit()

    def add_poses(self, poses: Iterable[Tuple[str, ]], commit: bool = True):
        self.conn.executemany('''
                INSERT or IGNORE INTO pos (name)
                VALUES (?)''', poses)
        if commit:
            self.conn.commit()

    def add_sentence_tokens(self, sentence: DatabaseSentence):
        """
        Add records about tokens
        Args:
            sentence: instance of DatabaseSentence class
        """
        lemmas = sentence.tokens_attr('lemma_', 'tuple')
        poses = sentence.tokens_attr('tag_', 'tuple')
        tokens_info = iter(sentence)
        try:
            self.add_lemmas(lemmas, commit=False)
            self.add_poses(poses, commit=False)
            self.conn.executemany('''
            INSERT INTO tokens (sent_id, token, whitespace, pos_in_sent, char_start, char_end, pos_id, lemma_id)
            VALUES (
            (SELECT sents.id FROM sents 
            LEFT JOIN texts 
            ON texts.id = sents.text_id 
            WHERE texts.filename = :filename 
            AND sents.pos_in_text = :sent_pos_in_text),
            :token,
            :whitespace, 
            :pos_in_sent,
            :char_start, 
            :char_end,
            (SELECT id FROM pos WHERE name = :pos),
            (SELECT id FROM lemmas WHERE name = :lemma))''', tokens_info)
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            print(e)

    def update_sentence_tokens_info(self, sentence: DatabaseSentence):
        lemmas = sentence.tokens_attr("lemma_", "tuple")
        poses = sentence.tokens_attr("tag_", "tuple")
        tokens_info = iter(sentence)
        try:
            self.add_lemmas(lemmas, commit=False)
            self.add_poses(poses, commit=False)
            self.conn.executemany(
                '''
                    UPDATE tokens
                    SET 
                    lemma_id = (SELECT id FROM lemmas WHERE name = :lemma),
                    pos_id = (SELECT id FROM pos WHERE name = :pos)
                    WHERE sent_id = (SELECT sents.id FROM sents 
                    LEFT JOIN texts 
                    ON texts.id = sents.text_id 
                    WHERE texts.filename = :filename 
                    AND sents.pos_in_text = :sent_pos_in_text)
                    AND pos_in_sent = :pos_in_sent''', tokens_info)
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            print(e)


if __name__ == '__main__':
    from mathematicon.config import DATA_PATH
    from pathlib import Path

    db_path = Path(DATA_PATH, 'mathematicon.db')

    db = UserDBHandler(db_path)
    print(db.get_user_by_uname('vknyazkova'))