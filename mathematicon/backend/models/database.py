import sqlite3


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


class WebDBHandler(DBHandler):

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


if __name__ == '__main__':
    from mathematicon.config import DATA_PATH
    from pathlib import Path

    db_path = Path(DATA_PATH, 'mathematicon.db')

    db = WebDBHandler(db_path)
    print(db.get_user_by_uname('vknyazkova'))