import os
import sqlite3
from typing import Iterable, Tuple, Union, List

from .custom_dataclasses import DatabaseToken, DatabaseSentence, DatabaseText


class DBHandler:
    conn = None

    def __init__(self,
                 db_path: Union[str, os.PathLike]):
        try:
            self.conn = sqlite3.connect(db_path, check_same_thread=False)
        except sqlite3.OperationalError:
            raise sqlite3.OperationalError(db_path)

    def __del__(self):
        self.conn.close()

    @staticmethod
    def dict_factory(cursor: sqlite3.Cursor, row):
        fields = [column[0] for column in cursor.description]
        return {key: value for key, value in zip(fields, row)}

    @staticmethod
    def one_column_factory(cursor: sqlite3.Cursor, row):
        return row[0]


class UserDBHandler(DBHandler):

    def get_user_by_uname(self,
                          username: str):
        cur = self.conn.execute('''
        SELECT * 
        FROM users
        WHERE username = (?)
        ''', (username,))
        cur.row_factory = self.dict_factory
        return cur.fetchone()

    def add_user(self,
                 username: str,
                 password: str,
                 salt, email):
        self.conn.execute('''
        INSERT INTO users (username, password, salt, email)
        VALUES (?, ?, ?, ?)''', (username, password, salt, email))
        self.conn.commit()

    def add_favs(self,
                 userid: int,
                 query: str,
                 query_type: int,
                 sent_id: int):
        self.conn.execute(
            '''INSERT INTO favourites (user_id, query, query_type, sent_id) 
            VALUES (?, ?, ?, ?)
            ''', (userid, query, query_type, sent_id)
        )
        self.conn.commit()

    def remove_fav(self,
                   userid: int,
                   sent_id: int):
        self.conn.execute(
            '''DELETE FROM favourites
            WHERE user_id = (?) AND sent_id = (?)''', (userid, sent_id)
        )
        self.conn.commit()


class TextDBHandler(DBHandler):

    def add_math_branch(self,
                        name: str,
                        commit: bool = True):
        self.conn.execute('''
        INSERT or IGNORE INTO math_branches (name)
        VALUES (?)''', (name, ))
        if commit:
            self.conn.commit()

    def add_text_level(self,
                       name: str,
                       commit: bool = True):
        self.conn.execute('''
                    INSERT or IGNORE INTO text_difficulty (name)
                    VALUES (?)''', (name,))
        if commit:
            self.conn.commit()

    def add_text(self,
                 text: DatabaseText):
        """
        Adds record about text to database or updates if filename exists
        Args:
            text: instance of DatabaseText class
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
            WHERE filename = :filename
            ''', text_info)
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            print(e)

    def add_sentence(self,
                     sentence: DatabaseSentence):
        """
        Adds information about sentence
        Args:
            sentence: instance of DatabaseSentence class
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
            :pos_in_text)
            ''', sentence_info)
            self.conn.commit()
        except sqlite3.IntegrityError as e:
            self.conn.rollback()
            print('This sentence is already in database')

    def add_lemmas(self,
                   lemmas: Iterable[Tuple[str, ]],
                   commit: bool = True):
        self.conn.executemany('''
        INSERT or IGNORE INTO lemmas (name)
        VALUES (?)''', lemmas)
        if commit:
            self.conn.commit()

    def add_poses(self,
                  poses: Iterable[Tuple[str, ]],
                  commit: bool = True):
        self.conn.executemany('''
                INSERT or IGNORE INTO pos (name)
                VALUES (?)''', poses)
        if commit:
            self.conn.commit()

    def add_sentence_tokens(self,
                            sentence: DatabaseSentence):
        """
        Add records about tokens
        Args:
            sentence: instance of DatabaseSentence class
        """
        try:
            lemmas = sentence.tokens_attr('lemma_', 'tuple')
            poses = sentence.tokens_attr('tag_', 'tuple')
            tokens_info = iter(sentence)
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
        except sqlite3.IntegrityError as e:
            self.conn.rollback()
            print('This tokens are already in database. If you want to update use update_sentence_tokens_info')

    def update_sentence_tokens_info(self,
                                    sentence: DatabaseSentence):
        try:
            lemmas = sentence.tokens_attr("lemma_", "tuple")
            poses = sentence.tokens_attr("tag_", "tuple")
            tokens_info = iter(sentence)
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


class WebDBHandler(DBHandler):
    def sents_with_query_words(self,
                               lemmatized_query: Iterable[str]) -> Iterable[dict]:
        pattern = '%' + '%'.join(lemmatized_query) + '%'
        cur = self.conn.execute('''
        SELECT sents.id, sents.lemmatized
        FROM sents
        WHERE sents.lemmatized LIKE ?''', (pattern,))
        cur.row_factory = self.dict_factory
        return cur.fetchall()

    def sent_info(self,
                  sent_id: int):
        cur = self.conn.execute('''
        SELECT sents.text_id, sents.pos_in_text, texts.youtube_link, sents.timecode
        FROM sents
        LEFT JOIN texts
        ON sents.text_id = texts.id
        WHERE sents.id = (?)         
        ''', (sent_id,))
        cur.row_factory = self.dict_factory
        return cur.fetchone()

    def sent_context(self,
                     text_id: int,
                     pos_in_text: int) -> Tuple[str, str]:
        cur = self.conn.execute('''
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

    def sent_token_info(self,
                        sent_id: int) -> List[dict]:
        cur = self.conn.execute('''
        SELECT tokens.token, tokens.whitespace, pos.name AS 'pos', lemmas.name AS 'lemma', tokens.char_start, tokens.char_end
        FROM tokens
        LEFT JOIN lemmas
        ON lemmas.id = tokens.lemma_id
        LEFT JOIN pos
        ON pos.id = tokens.pos_id
        WHERE tokens.sent_id = (?)
        ORDER BY tokens.pos_in_sent
        ''', (sent_id,))
        cur.row_factory = self.dict_factory
        return cur.fetchall()

    def get_user_favourites(self,
                            userid: int,
                            search_type: int):
        cur = self.conn.execute('''
        SELECT favourites.sent_id
        FROM favourites
        WHERE favourites.user_id = (?) AND favourites.query_type = (?)
        ''', (userid, search_type))
        cur.row_factory = self.one_column_factory
        return cur.fetchall()



