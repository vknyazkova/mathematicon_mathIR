import sqlite3
from contextlib import closing

from ..model import MathLecture


class LectureRepository:
    def __init__(self, dp_path: str):
        self._dp_path = dp_path

    def get_math_branch_id(self,
                           conn: sqlite3.Connection,
                           name: str) -> int:
        cur = conn.cursor()
        cur.execute('''SELECT name
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

    def get_text_difficulty_id(self,
                               conn: sqlite3.Connection,
                               name: str) -> int:
        cur = conn.cursor()
        cur.execute('''SELECT name
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

    def add_lecture(self, lecture: MathLecture) -> MathLecture:
        with closing(sqlite3.connect(self._dp_path)) as conn:
            cur = conn.cursor()
            math_branch_id = self.get_math_branch_id(conn, lecture.math_branch)
            text_difficulty_id = self.get_text_difficulty_id(conn, lecture.difficulty_level)
            cur.execute('''
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
            lecture.lecture_id = cur.fetchone()
        return lecture
