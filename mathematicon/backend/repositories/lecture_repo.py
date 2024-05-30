import sqlite3
from typing import Optional

from ..model import MathLecture


class LectureRepository:
    def __init__(self,
                 db_path: str,
                 db_conn: Optional[sqlite3.Connection] = None):
        self.dp_path = db_path
        self.conn = db_conn

    def connect(self):
        if self.conn is None:
            self.conn = sqlite3.connect(self.dp_path, check_same_thread=True)

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

        # Create math_branches table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS math_branches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            )
            ''')

        # Create text_difficulty table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS text_difficulty (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            )
            ''')

        # Create texts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS texts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                filename TEXT UNIQUE,
                youtube_link TEXT UNIQUE,
                timecode_start TEXT,
                timecode_end TEXT,
                math_branch_id INTEGER,
                level_id INTEGER,
                FOREIGN KEY (math_branch_id) REFERENCES math_branches (id) ON DELETE SET NULL ON UPDATE CASCADE,
                FOREIGN KEY (level_id) REFERENCES text_difficulty (id) ON DELETE SET NULL ON UPDATE CASCADE
            )
            ''')

        self.conn.commit()

    def _get_math_branch_id(self,
                            name: str) -> int:
        cur = self.conn.cursor()
        cur.execute('''SELECT id
        FROM math_branches
        WHERE name = (?)''', (name, ))
        id_ = cur.fetchone()
        if not id_:
            cur.execute('''
            INSERT INTO math_branches (name)
            VALUES (?)
            RETURNING id''', (name, ))
            id_ = cur.fetchone()
        return id_[0]

    def _get_text_difficulty_id(self,
                                name: str) -> int:
        cur = self.conn.cursor()
        cur.execute('''SELECT id
                FROM text_difficulty
                WHERE name = (?)''', (name,))
        id_ = cur.fetchone()
        if not id_:
            cur.execute('''
                    INSERT INTO text_difficulty (name)
                    VALUES (?)
                    RETURNING id''', (name,))
            id_ = cur.fetchone()
        return id_[0]

    def add_lecture(self,
                    lecture: MathLecture) -> MathLecture:
        self.connect()
        with self.conn:
            math_branch_id = self._get_math_branch_id(lecture.math_branch)
            text_difficulty_id = self._get_text_difficulty_id(lecture.difficulty_level)
            cur = self.conn.execute('''
                                INSERT INTO texts (title, filename, youtube_link, timecode_start, timecode_end, math_branch_id, level_id)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                                RETURNING id''', (
                lecture.title,
                lecture.filename,
                lecture.youtube_link,
                lecture.timecode_start,
                lecture.timecode_end,
                math_branch_id,
                text_difficulty_id
            ))
            lecture.lecture_id = cur.fetchone()[0]
        return lecture

    def get_lecture_id_from_filename(self,
                                     filename: str) -> Optional[int]:
        self.connect()
        with self.conn:
            cur = self.conn.execute('''
            SELECT id
            FROM texts
            WHERE filename = ?''', (filename, ))
            return cur.fetchone()[0]
