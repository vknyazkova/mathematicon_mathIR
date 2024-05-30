import unittest
from mathematicon.backend.repositories.annotation_repo import AnnotationRepository
from mathematicon.backend.model import AnnotationFragment


class TestAnnotationRepository(unittest.TestCase):

    def setUp(self):
        self.db_path = ':memory:'
        self.repository = AnnotationRepository(self.db_path)
        self.repository.create_tables()
        self.annotation_fragment = AnnotationFragment(sentence_id=1, char_start=0, char_end=10)

    def test_create_tables(self):
        self.repository.connect()
        cursor = self.repository.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='annot_fragment';")
        table = cursor.fetchone()
        self.assertIsNotNone(table)
        self.assertEqual(table[0], 'annot_fragment')

    def test_add_annot_fragment(self):
        self.repository.add_annot_fragment(self.annotation_fragment)
        self.assertIsNotNone(self.annotation_fragment.annotation_id)

        cursor = self.repository.conn.cursor()
        cursor.execute('''
            SELECT id, sent_id, char_start, char_end
            FROM annot_fragment
            WHERE id = ?''', (self.annotation_fragment.annotation_id,))
        row = cursor.fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row[1], self.annotation_fragment.sentence_id)
        self.assertEqual(row[2], self.annotation_fragment.char_start)
        self.assertEqual(row[3], self.annotation_fragment.char_end)

    def test_get_annot_fragment_by_id(self):
        self.repository.add_annot_fragment(self.annotation_fragment)
        fetched_fragment = self.repository.get_annot_fragment_by_id(self.annotation_fragment.annotation_id)
        self.assertIsNotNone(fetched_fragment)
        self.assertEqual(fetched_fragment.annotation_id, self.annotation_fragment.annotation_id)
        self.assertEqual(fetched_fragment.sentence_id, self.annotation_fragment.sentence_id)
        self.assertEqual(fetched_fragment.char_start, self.annotation_fragment.char_start)
        self.assertEqual(fetched_fragment.char_end, self.annotation_fragment.char_end)


if __name__ == '__main__':
    unittest.main()
