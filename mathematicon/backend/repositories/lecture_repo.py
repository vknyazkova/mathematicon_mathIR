import sqlite3
from contextlib import closing
from typing import Optional

from ..model import MathLecture


class LectureRepository:
    def __init__(self,
                 dp_path: str,
                 db_conn: Optional[sqlite3.Connection] = None):
        self.dp_path = dp_path
        self.conn = db_conn

    def connect(self):
        if self.conn is None:
            self.conn = sqlite3.connect(self.dp_path)

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
            CREATE TABLE math_branches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            )
            ''')

        # Create text_difficulty table
        cursor.execute('''
            CREATE TABLE text_difficulty (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            )
            ''')

        # Create texts table
        cursor.execute('''
            CREATE TABLE texts (
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


if __name__ == '__main__':
    db_path = ':memory:'
    conn = sqlite3.connect(db_path)
    lecture_repo = LectureRepository(db_path, conn)

    lecture_repo.create_tables()
    cur = conn.execute('''SELECT name FROM sqlite_master WHERE type='table';''')
    print(cur.fetchall())

    lecture1 = MathLecture(
        title="Sample Lecture",
        filename="sample.mp4",
        youtube_link="https://youtube.com/sample",
        timecode_start="00:00:00",
        timecode_end="01:00:00",
        math_branch="Algebra",
        difficulty_level="Intermediate"
    )

    lecture2 = MathLecture(
        title="Sample Lecture2",
        filename="sample2.mp4",
        youtube_link="https://youtube.com/sample2",
        timecode_start="00:00:00",
        timecode_end="01:10:00",
        math_branch="Geometry",
        difficulty_level="Intermediate"
    )
    try:
        lecture1 = lecture_repo.add_lecture(lecture1)
        print(lecture1)
        lecture2 = lecture_repo.add_lecture(lecture2)
        print(lecture2)
    except Exception as e:
        cur = conn.execute('''SELECT * FROM math_branches''')
        print(cur.fetchall())
    conn.close()