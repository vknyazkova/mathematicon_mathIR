import sqlite3
from typing import Iterable


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
    def add_math_branch(self, name: str) -> int:
        with self.conn:
            cur = self.conn.execute('''
            INSERT or IGNORE INTO math_branches (name)
            VALUES (?)
            RETURNING id''', (name,))
            added_id = cur.fetchone()

            if not added_id:
                self.conn.execute('''
                SELECT id
                FROM math_branches
                WHERE name = (?)''', (name,))
                added_id = cur.fetchone()
        return added_id[0]

    def add_text_level(self, name) -> int:
        with self.conn:
            cur = self.conn.execute('''
                        INSERT or IGNORE INTO text_difficulty (name)
                        VALUES (?)
                        RETURNING id''', (name,))
            added_id = cur.fetchone()

            if not added_id:
                self.conn.execute('''
                            SELECT id
                            FROM text_difficulty
                            WHERE name = (?)''', (name,))
                added_id = cur.fetchone()
        return added_id[0]

    def add_text(self, text_info: dict) -> int:
        """
        Add record about text to database
        Args:
            text_info: dict with keys
                title: text title
                branch: math branch
                level: difficulty level
                filename: name where this text is stored
                yb_link: link to youtube video

        Returns: inserted text id

        """
        with self.conn:
            text_info['branch'] = self.add_math_branch(text_info['branch'])
            text_info['level'] = self.add_text_level(text_info['level'])

            cur = self.conn.execute('''
            INSERT or IGNORE INTO texts (title, filename, youtube_link, level_id, math_branch_id)
            VALUES (:title, :filename, :yb_link, :level, :branch)
            RETURNING id''', text_info)
            added_id = cur.fetchone()[0]

            if not added_id:
                cur = self.conn.execute('''
                            SELECT id
                            FROM texts
                            WHERE filename = :filename''', text_info)
                added_id = cur.fetchone()[0]
        return added_id

    def get_text_id(self, filename: str) -> int:
        cur = self.conn.execute('''
        SELECT id
        FROM texts
        WHERE filename = ?''', (filename,))

        return cur.fetchone()[0]

    def add_sentence(self, sentence_info: dict) -> int:
        """
        Adds information about sentence
        Args:
            sentence_info: dictionary, that contains following keys:
                text_id: text_id of the sentence
                sent: sentence itself
                lemmatized: lemmatized sentence
                pos_in_text: sequence number of sentence in the text
        Returns: sentence id

        """
        with self.conn:
            cur = self.conn.execute('''
            INSERT INTO sents (text_id, sent, lemmatized, pos_in_text)
            VALUES (:text_id, :sent, :lemmatized, :pos_in_text)
            RETURNING id''', sentence_info)

        return cur.fetchone()[0]

    def add_lemma(self, lemma, commit: bool = True):
        cur = self.conn.execute('''
        INSERT or IGNORE INTO lemmas (name)
        VALUES (?)
        RETURNING id''', (lemma,))
        added_id = cur.fetchone()

        if not added_id:
            self.conn.execute('''
            SELECT id
            FROM lemmas
            WHERE name = (?)''', (lemma,))
            added_id = cur.fetchone()
        if commit:
            self.conn.commit()
        return added_id[0]

    def add_pos(self, pos, commit: bool = True):
        cur = self.conn.execute('''
                INSERT or IGNORE INTO pos (name)
                VALUES (?)
                RETURNING id''', (pos,))
        added_id = cur.fetchone()

        if not added_id:
            self.conn.execute('''
                    SELECT id
                    FROM lemmas
                    WHERE name = (?)''', (pos,))
            added_id = cur.fetchone()
        if commit:
            self.conn.commit()
        return added_id[0]

    def add_token(self, token_info):
        """
        Add grammar annotation for token
        Args:
            token_info: dictionary
                token: token itself
                whitespace: 1 if there is whitespace after and 0 otherwise
                pos_in_text: sequence number of token in text
                char_start:
                char_end:
                pos: pos tag
                lemma: token lemma
                sent_id: id of the sentence

        Returns:

        """
        with self.conn:
            token_info['pos'] = self.add_pos(token_info['pos'], commit=False)
            token_info['lemma'] = self.add_lemma(token_info['lemma'], commit=False)
            self.conn.execute('''
            INSERT INTO tokens (sent_id, token, whitespace, lemma_id, pos_id, pos_in_text, char_start, char_end)
            VALUES (:sent_id, :token, :whitespace, :lemma, :pos, :pos_in_text, :char_start, :char_end)''', token_info)

    def get_sent_id(self, text_id: int, pos_in_text: int):
        cur = self.conn.execute('''
        SELECT id
        FROM sents
        WHERE text_id = (?) AND pos_in_text = (?)''', (text_id, pos_in_text))
        return cur.fetchone()[0]

    # def update_text_grammar_info(self, filename: str, new_grammar: Iterable[Iterable[dict]]):
    #     text_id = self.get_text_id(filename)
    #     with self.conn:
    #         for i, sent in new_grammar:
    #             sent_id = self.get_sent_id(text_id, i)
    #             for token_info in sent:
    #                 token_info['sent_id'] = sent_id
    #                 token_info['lemma'] = self.add_lemma(token_info['lemma'], commit=False)
    #                 token_info['pos'] = self.add_pos(token_info['pos'], commit=False)
    #                 self.conn.execute('''
    #                 UPDATE
    #                     lemma_id = : lemma,
    #                     pos_id = :pos,
    #                 WHERE sent''')




if __name__ == '__main__':
    from mathematicon.config import DATA_PATH
    from pathlib import Path

    db_path = Path(DATA_PATH, 'mathematicon.db')

    db = UserDBHandler(db_path)
    print(db.get_user_by_uname('vknyazkova'))