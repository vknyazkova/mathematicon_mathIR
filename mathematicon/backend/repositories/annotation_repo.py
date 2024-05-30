from typing import Optional
import sqlite3

from ..model import AnnotationFragment


class AnnotationRepository:
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
        with self.conn:
            self.conn.execute('''
            CREATE TABLE IF NOT EXISTS annot_fragment (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sent_id INTEGER,
                char_start INTEGER,
                char_end INTEGER,
                UNIQUE(sent_id, char_start, char_end),
                FOREIGN KEY(sent_id) REFERENCES sents(id) ON DELETE CASCADE ON UPDATE CASCADE
            )''')

    @staticmethod
    def annot_fragment_mapping_factory(cursor: sqlite3.Cursor,
                                       row):
        fields = [column[0] for column in cursor.description]
        attrs = {key: value for key, value in zip(fields, row)}
        return AnnotationFragment(**attrs)

    def get_annot_frag_id(self, annotation_frag: AnnotationFragment) -> Optional[int]:
        self.connect()
        cur = self.conn.execute('''
        SELECT id FROM annot_fragment 
        WHERE sent_id = ? AND char_start = ? AND char_end = ?''', (annotation_frag.sentence_id, annotation_frag.char_start, annotation_frag.char_end))
        res = cur.fetchone()
        if res:
            return res[0]
        return None

    def add_annot_fragment(self, annot_fragment: AnnotationFragment) -> AnnotationFragment:
        self.connect()
        with self.conn:
            id = self.get_annot_frag_id(annot_fragment)
            if not id:
                cur = self.conn.execute('''
                    INSERT INTO annot_fragment (sent_id, char_start, char_end) 
                    VALUES (?, ?, ?)
                    RETURNING id''', (annot_fragment.sentence_id, annot_fragment.char_start, annot_fragment.char_end))
                id = cur.fetchone()[0]
            annot_fragment.annotation_id = id
        return annot_fragment

    def has_related_entries(self, annotation_id: int) -> bool:
        # Check for related entries in other tables
        self.connect()
        with self.conn:
            # Example query, adjust based on your schema
            cur = self.conn.execute('''
            SELECT COUNT(*) 
            FROM math_entities
            WHERE frag_id = ?''', (annotation_id,))
            count = cur.fetchone()[0]

            cur = self.conn.execute('''
                        SELECT COUNT(*) 
                        FROM math_annotation
                        WHERE annot_frag_id = ?''', (annotation_id,))
            count += cur.fetchone()[0]
        return count > 0

    def get_annot_fragment_by_id(self, annot_fragment_id: id) -> AnnotationFragment:
        self.connect()
        with self.conn:
            cur = self.conn.execute('''
            SELECT 
            id AS annotation_id,
            sent_id AS sentence_id, 
            char_start AS char_start, 
            char_end AS char_end
            FROM annot_fragment
            WHERE id = ?''', (annot_fragment_id,))
            cur.row_factory = self.annot_fragment_mapping_factory
            return cur.fetchone()

    def delete_annot_fragment_by_id(self, annotation_id: int):
        self.connect()
        with self.conn:
            self.conn.execute('DELETE FROM annot_fragment WHERE id = ?', (annotation_id,))

    def conditional_delete_annot_fragment_by_id(self, annotation_id: int):
        if not self.has_related_entries(annotation_id):
            self.delete_annot_fragment_by_id(annotation_id)

