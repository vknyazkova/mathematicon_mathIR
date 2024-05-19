import unittest
import sqlite3

from mathematicon.backend.repositories.lecture_repo import LectureRepository
from mathematicon.backend.model import MathLecture


class TestLectureRepository(unittest.TestCase):

    def setUp(self):
        self.conn = sqlite3.connect(':memory:')
        self.repo = LectureRepository(db_path=':memory:', db_conn=self.conn)
        self.repo.create_tables()

    def tearDown(self):
        self.conn.close()

    def test_add_lectures_without_duplicates(self):
        # Adding multiple lectures
        lecture1 = MathLecture(
            title="Sample Lecture 1",
            filename="sample1.mp4",
            youtube_link="https://youtube.com/sample1",
            timecode_start="0",
            timecode_end="6696",
            math_branch="Algebra",
            difficulty_level="Intermediate"
        )
        lecture2 = MathLecture(
            title="Sample Lecture 2",
            filename="sample2.mp4",
            youtube_link="https://youtube.com/sample2",
            timecode_start="5",
            timecode_end="6632",
            math_branch="Geometry",
            difficulty_level="Intermediate"
        )
        lecture3 = MathLecture(
            title="Sample Lecture 3",
            filename="sample3.mp4",
            youtube_link="https://youtube.com/sample3",
            timecode_start="15",
            timecode_end="10387",
            math_branch="Algebra",
            difficulty_level="Advanced"
        )

        self.repo.add_lecture(lecture1)
        self.repo.add_lecture(lecture2)
        self.repo.add_lecture(lecture3)

        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM math_branches")
        math_branch_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM text_difficulty")
        text_difficulty_count = cur.fetchone()[0]

        self.assertEqual(math_branch_count, 2, "There should be 2 unique math branches.")
        self.assertEqual(text_difficulty_count, 2, "There should be 2 unique text difficulties.")

    def test_prevent_duplicate_youtube_link(self):
        lecture = MathLecture(
            title="Sample Lecture",
            filename="sample.mp4",
            youtube_link="https://youtube.com/sample",
            timecode_start="00",
            timecode_end="6692",
            math_branch="Algebra",
            difficulty_level="Intermediate"
        )

        self.repo.add_lecture(lecture)

        with self.assertRaises(sqlite3.IntegrityError):
            # Attempt to add the same lecture again
            self.repo.add_lecture(lecture)

        # Check if the transaction was rolled back successfully
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM texts WHERE youtube_link = ?", (lecture.youtube_link,))
        self.assertEqual(cur.fetchone()[0], 1, "There should only be one lecture with the given youtube link.")

        # Ensure no orphaned entries in related tables
        cur.execute("SELECT COUNT(*) FROM math_branches")
        math_branch_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM text_difficulty")
        text_difficulty_count = cur.fetchone()[0]

        self.assertEqual(math_branch_count, 1, "There should be 1 math branch.")
        self.assertEqual(text_difficulty_count, 1, "There should be 1 text difficulty.")


if __name__ == '__main__':
    unittest.main()
