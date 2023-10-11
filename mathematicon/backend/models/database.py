import sqlite3


class DBHandler:
    conn = None

    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)

    def __del__(self):
        self.conn.close()


class WebDBHandler(DBHandler):

    def get_user_by_uname(self, username):
        ...