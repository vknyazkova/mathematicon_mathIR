from typing import Optional, List
import sqlite3

from ..model import UserInfo, SearchHistory, Favorites


class UserRepository:
    def __init__(self,
                 db_path: str,
                 conn: Optional[sqlite3.Connection] = None):
        self.db_path = db_path
        self.conn = conn

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

    @staticmethod
    def favorites_mapper(cursor: sqlite3.Cursor,
                         row) -> Favorites:
        fields = [column[0] for column in cursor.description]
        attrs = {key: value for key, value in zip(fields, row)}
        return Favorites(**attrs)

    @staticmethod
    def user_mapper(cursor: sqlite3.Cursor,
                    row) -> UserInfo:
        fields = [column[0] for column in cursor.description]
        attrs = {key: value for key, value in zip(fields, row)}
        return UserInfo(**attrs)

    @staticmethod
    def search_history_mapper(cursor: sqlite3.Cursor,
                              row) -> SearchHistory:
        fields = [column[0] for column in cursor.description]
        attrs = {key: value for key, value in zip(fields, row)}
        return SearchHistory(**attrs)

    def create_tables(self):
        self.connect()
        cursor = self.conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            salt BLOB NOT NULL
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS favourites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            query TEXT NOT NULL,
            link TEXT NOT NULL,
            sent_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,
            FOREIGN KEY (sent_id) REFERENCES sents(id) ON DELETE SET NULL ON UPDATE CASCADE
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            query TEXT NOT NULL,
            link TEXT NOT NULL,
            time TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE
        )
        ''')
        self.conn.commit()

    def add_user(self, user: UserInfo) -> UserInfo:
        self.connect()
        with self.conn:
            cur = self.conn.cursor()
            cur.execute('''
            INSERT INTO users (username, email, password, salt) 
            VALUES (?, ?, ?, ?)
            RETURNING id''', (user.username, user.email, user.password_hash, user.salt))
            user.user_id = cur.fetchone()[0]
        return user

    def update_history(self,
                       search_history: SearchHistory,
                       history_limit: int = 5):
        self.connect()
        with self.conn:
            cursor = self.conn.cursor()

            # Insert the new search history entry
            cursor.execute('''
                INSERT INTO user_history (user_id, query, link, time)
                VALUES (?, ?, ?, ?)
            ''', (search_history.user_id, search_history.query, search_history.link, search_history.timestamp))

            # Check the count of the user's search history
            cursor.execute('''
                SELECT COUNT(*) FROM user_history
                WHERE user_id = ?
            ''', (search_history.user_id,))
            count = cursor.fetchone()[0]

            # If the count exceeds the history limit, delete the oldest entries
            if count > history_limit:
                cursor.execute('''
                    DELETE FROM user_history
                    WHERE id IN (
                        SELECT id FROM user_history
                        WHERE user_id = ?
                        ORDER BY time
                        LIMIT ?
                    )
                ''', (search_history.user_id, count - history_limit))

    def get_user_search_history(self, user: UserInfo) -> List[SearchHistory]:
        self.connect()
        with self.conn:
            cur = self.conn.execute('''
            SELECT
                id AS search_id,
                user_id AS user_id,
                time AS timestamp,
                query AS query,
                link AS link 
            FROM user_history
            WHERE user_id = ?''', (user.user_id,))
            cur.row_factory = self.search_history_mapper
            return cur.fetchall()

    def add_favorites(self, favorites: Favorites):
        self.connect()
        with self.conn:
            self.conn.execute(
                """INSERT INTO favourites (user_id, query, link, sent_id) 
                VALUES (:user_id, :query, :link, :sent_id)""",
                {'user_id': favorites.user_id,
                 'query': favorites.query,
                 'link': favorites.link,
                 'sent_id': favorites.sentence_id}
            )

    def remove_favorites(self, favorites: Favorites):
        self.connect()
        with self.conn:
            self.conn.execute(
                '''
                DELETE FROM favourites
                WHERE user_id = (?) AND sent_id = (?)''', (favorites.user_id, favorites.sentence_id)
            )

    def get_user_favorites(self,
                           user: UserInfo) -> List[Favorites]:
        self.connect()
        cur = self.conn.execute('''
        SELECT 
            id AS favorite_id, 
            user_id AS user_id, 
            query AS query, 
            link AS link,
            sent_id AS sentence_id
        FROM favourites
        WHERE user_id = ?''', (user.user_id,))
        cur.row_factory = self.favorites_mapper
        return cur.fetchall()

    def get_by_username(self, username: str) -> UserInfo:
        self.connect()
        cur = self.conn.execute('''
        SELECT 
            id AS user_id,
            username AS username,
            email AS email,
            password AS password_hash,
            salt AS salt
        FROM users
        WHERE username = ?''', (username, ))
        cur.row_factory = self.user_mapper
        return cur.fetchone()


