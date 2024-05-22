import os
import sqlite3
from typing import Iterable, Tuple, Union, List, Dict, Optional, Any
from dataclasses import asdict
from datetime import datetime
from contextlib import contextmanager

from .db_data_models import (
    DatabaseSentence,
    DatabaseText,
    Mathtag,
    MathtagAttrs,
    DatabaseMorph,
    AnnotFrag,
    MathEntity,
    MathEntityRelated,
    DatabaseToken
)


class DBHandler:
    conn = None

    def __init__(self,
                 db_path: Union[str, os.PathLike]):
        try:
            self.conn = sqlite3.connect(db_path, check_same_thread=False)
        except sqlite3.OperationalError:
            raise sqlite3.OperationalError(db_path)

    def __del__(self):
        self.conn.close()

    @contextmanager
    def transaction(self, raise_exception: bool = False):
        try:
            yield self.conn
            self.conn.commit()
        except sqlite3.IntegrityError as e:
            self.conn.rollback()
            if raise_exception:
                raise e
            else:
                print(f"Error during query execution: {e.__class__.__name__} - {str(e)}")
        except Exception as e:
            self.conn.close()
            raise e

    @staticmethod
    def dict_factory(cursor: sqlite3.Cursor, row):
        fields = [column[0] for column in cursor.description]
        return {key: value for key, value in zip(fields, row)}

    @staticmethod
    def one_column_factory(cursor: sqlite3.Cursor, row):
        return row[0]


class TextDBHandler(DBHandler):

    def _get_math_branch_id(self, name: str) -> Optional[Tuple[int, ]]:
        cur = self.conn.execute('''
        SELECT id 
        FROM math_branches
        WHERE name = (?)''', (name,))
        return cur.fetchone()

    def _add_math_branch(self, name: str, commit: bool = True) -> Tuple[int, ]:
        cur = self.conn.execute("""
                    INSERT or IGNORE INTO math_branches (name)
                    VALUES (?)
                    RETURNING id""", (name,))
        if commit:
            self.conn.commit()
        return cur.fetchone()

    def math_branch_id(self, name: str, commit: bool = True) -> int:
        math_branch_id = self._get_math_branch_id(name)
        if not math_branch_id:
            math_branch_id = self._add_math_branch(name, commit=commit)
        return math_branch_id[0]

    def _get_text_level_id(self, name: str) -> Optional[Tuple[int,]]:
        cur = self.conn.execute("""
        SELECT id 
        FROM text_difficulty
        WHERE name = (?)""", (name, ))
        return cur.fetchone()

    def _add_text_level(self,
                        name: str,
                        commit: bool = True) -> Tuple[int, ]:
        cur = self.conn.execute(
            """
            INSERT or IGNORE INTO text_difficulty (name)
            VALUES (?)
            RETURNING id""", (name, ))
        if commit:
            self.conn.commit()
        return cur.fetchone()

    def text_level_id(self, name: str, commit: bool = True) -> int:
        text_level_id = self._get_text_level_id(name)
        if not text_level_id:
            text_level_id = self._add_text_level(name, commit=commit)
        return text_level_id[0]

    def add_text(self, text: DatabaseText, status: str = 'texts'):
        with self.transaction():
            math_branch_id = self.math_branch_id(text.branch, commit=False)
            text_difficulty_id = self.text_level_id(text.level, commit=False)
            self.conn.execute("""
            INSERT INTO texts (title, filename, youtube_link, math_branch_id, level_id, status_id, timecode_start, timecode_end)
            VALUES (
            :title,
            :filename, 
            :yb_link,
            :branch_id,
            :level_id, 
            :status,
            :timecode_start, 
            :timecode_end)
            ON CONFLICT (filename)
            DO UPDATE SET 
            title = :title,
            youtube_link = :yb_link,
            level_id = :level_id,
            math_branch_id = :branch_id,
            timecode_start = :timecode_start,
            timecode_end = :timecode_end""", vars(text) | {
                'branch_id': math_branch_id, 'level_id': text_difficulty_id, 'status': status
            })

    def update_text_status(self,
                           filename: str,
                           new_status_name: str,
                           commit: bool = True):
        self.conn.execute("""
        UPDATE texts
        SET status_id = (SELECT id FROM annotation_status WHERE name = (?))
        WHERE filename = (?)
        """, (new_status_name, filename))

        if commit:
            self.conn.commit()

    def add_sentence(self,
                     sentence: DatabaseSentence,
                     status: str = 'sents'):
        with self.transaction():
            self.conn.execute("""
            INSERT INTO sents (text_id, sent, lemmatized, pos_in_text)
            VALUES (
            (SELECT id FROM texts WHERE filename = :filename), 
            :sent_text, 
            :lemmatized, 
            :pos_in_text)""", vars(sentence))
            self.update_text_status(sentence.filename, status)

    def _get_lemma_id(self, lemma: str) -> Optional[Tuple[int, ]]:
        cur = self.conn.execute("""
        SELECT id
        FROM lemmas
        WHERE name = (?)""", (lemma, ))
        return cur.fetchone()

    def _add_lemma(self,
                   lemma: str,
                   commit: bool = True) -> Tuple[int, ]:
        cur = self.conn.execute("""
                    INSERT INTO lemmas (name)
                    VALUES (?)
                    RETURNING id""", (lemma,))
        if commit:
            self.conn.commit()
        return cur.fetchone()

    def lemma_id(self,
                 lemma: str,
                 commit: bool = True) -> int:
        lemma_id = self._get_lemma_id(lemma)
        if not lemma_id:
            lemma_id = self._add_lemma(lemma, commit)
        return lemma_id[0]

    def _get_pos_id(self, pos_tag: str) -> Optional[Tuple[int, ]]:
        cur = self.conn.execute("""
        SELECT id 
        FROM pos
        WHERE name = (?)""", (pos_tag, ))
        return cur.fetchone()

    def _add_pos(self,
                 pos_tag: str,
                 commit: bool = True) -> Tuple[int, ]:
        cur = self.conn.execute("""
                    INSERT INTO pos (name)
                    VALUES (?)
                    RETURNING id""", (pos_tag, ))
        if commit:
            self.conn.commit()

        return cur.fetchone()

    def pos_id(self,
               pos_tag: str,
               commit: bool = True) -> int:
        pos_id = self._get_pos_id(pos_tag)
        if not pos_id:
            pos_id = self._add_pos(pos_tag, commit)
        return pos_id[0]

    def _get_morph_category_id(self,
                               category: str) -> Optional[Tuple[int, ]]:
        cur = self.conn.execute("""
        SELECT id 
        FROM morph_categories
        WHERE name = (?)""", (category, ))
        return cur.fetchone()

    def _add_morph_category(self,
                            category: str,
                            commit: bool = True) -> Tuple[int, ]:
        cur = self.conn.execute("""
                    INSERT INTO morph_categories (name)
                    VALUES (?)
                    RETURNING id""", (category, ))
        if commit:
            self.conn.commit()
        return cur.fetchone()

    def morph_category_id(self,
                          category: str,
                          commit: bool = True) -> int:
        cat_id = self._get_morph_category_id(category)
        if not cat_id:
            cat_id = self._add_morph_category(category, commit)
        return cat_id[0]

    def _get_morph_value_id(self,
                            value: str) -> Optional[Tuple[int, ]]:
        cur = self.conn.execute("""
        SELECT id 
        FROM morph_values
        WHERE name = (?)""", (value, ))
        return cur.fetchone()

    def _add_morph_value(self,
                         value: str,
                         commit: bool = True) -> Tuple[int, ]:
        cur = self.conn.execute("""
                    INSERT INTO morph_values (name)
                    VALUES (?)
                    RETURNING id""", (value, ))
        if commit:
            self.conn.commit()
        return cur.fetchone()

    def morph_value_id(self,
                       value: str,
                       commit: bool = True) -> int:
        val_id = self._get_morph_value_id(value)
        if not val_id:
            val_id = self._add_morph_value(value, commit)
        return val_id[0]

    def _add_token_morph(self,
                         token_id: int,
                         morph_annot: Iterable[DatabaseMorph],
                         commit: bool = True):
        for morph in morph_annot:
            cat_id = self.morph_category_id(morph.category, commit=commit)
            val_id = self.morph_value_id(morph.value, commit=commit)
            self.conn.execute("""
            INSERT or IGNORE INTO morph_features (token_id, category_id, value_id) 
            VALUES (?, ?, ?)""", (token_id, cat_id, val_id))

        if commit:
            self.conn.commit()

    def _add_token_info(self,
                        token: DatabaseToken,
                        commit: bool = True):
        pos_id = self.pos_id(token.pos, commit=commit)
        lemma_id = self.lemma_id(token.lemma, commit=commit)
        cur = self.conn.execute("""
        INSERT INTO tokens (sent_id, token, whitespace, pos_in_sent, char_start, char_end, pos_id, lemma_id)
        VALUES (
        (SELECT sents.id FROM sents 
        LEFT JOIN texts 
        ON texts.id = sents.text_id 
        WHERE texts.filename = :filename 
        AND sents.pos_in_text = :sent_pos_in_text),
        :token,
        :whitespace, 
        :pos_in_sent,
        :char_start, 
        :char_end,
        :pos_id,
        :lemma_id)
        RETURNING id""", vars(token) | {'pos_id': pos_id, 'lemma_id': lemma_id})
        token_id = cur.fetchone()[0]
        self._add_token_morph(token_id, token.morph, commit=commit)

        if commit:
            self.conn.commit()

    def add_sentence_tokens(self, sentence: DatabaseSentence):
        with self.transaction():
            for token in sentence:
                self._add_token_info(token, commit=False)

    def _del_token_morph(self,
                         token_id: int,
                         commit: bool = True):
        self.conn.execute("""
        DELETE FROM morph_features
        WHERE token_id = (?)""", (token_id, ))

        if commit:
            self.conn.commit()

    def _get_token_id(self,
                      token: DatabaseToken):
        cur = self.conn.execute("""
        SELECT tokens.id
        FROM tokens
        LEFT JOIN sents
        ON tokens.sent_id = sents.id
        LEFT JOIN texts
        ON sents.text_id = texts.id
        WHERE texts.filename = :filename
        AND sents.pos_in_text = :sent_pos_in_text
        AND tokens.pos_in_sent = :pos_in_sent""", vars(token))

        return cur.fetchone()[0]

    def _update_token_morph(self,
                            token_id: int,
                            token_morph: Iterable[DatabaseMorph],
                            commit: bool = True):
        self._del_token_morph(token_id, commit=commit)
        self._add_token_morph(token_id, token_morph, commit=commit)

    def _update_token_info(self,
                           token: DatabaseToken,
                           commit: bool = True):
        token_id = self._get_token_id(token)
        lemma_id = self._get_lemma_id(token.lemma)[0]
        pos_id = self._get_pos_id(token.pos)[0]
        self._update_token_morph(token_id, token.morph, commit=commit)
        self.conn.execute("""
        UPDATE tokens
        SET 
        lemma_id = (?),
        pos_id = (?)
        WHERE id = (?)""", (lemma_id, pos_id, token_id))

        if commit:
            self.conn.commit()

    def update_sentence_grammar_annotation(self,
                                           sentence: DatabaseSentence):
        with self.transaction():
            for token in sentence:
                self._update_token_info(token, commit=False)


class MathDBHandler(DBHandler):

    def _get_lang_id(self, lang_name: str) -> Optional[Tuple[int, ]]:
        cur = self.conn.execute("""
        SELECT id
        FROM langs
        WHERE name = (?)""", (lang_name,))
        return cur.fetchone()

    def _add_lang(self,
                  lang: str,
                  commit: bool = True) -> Tuple[int, ]:
        cur = self.conn.execute("""
                    INSERT INTO langs (name)
                    VALUES (?)
                    RETURNING id""", (lang, ))
        if commit:
            self.conn.commit()
        return cur.fetchone()

    def lang_id(self,
                lang_name: str,
                commit: bool = True) -> int:
        lang_id = self._get_lang_id(lang_name)
        if not lang_id:
            lang_id = self._add_lang(lang_name, commit)
        return lang_id[0]

    def _get_tag_id(self,
                    inception_id: str) -> Optional[Tuple[int, ]]:
        cur = self.conn.execute("""
        SELECT id
        FROM math_tags
        WHERE inception_id = (?)""", (inception_id, ))

        return cur.fetchone()

    def _add_inception_tag(self,
                           inception_tag: str,
                           commit: bool = True) -> Tuple[int, ]:
        cur = self.conn.execute("""
                    INSERT INTO math_tags (inception_id)
                    VALUES (?)
                    RETURNING id""", (inception_tag, ))
        if commit:
            self.conn.commit()
        return cur.fetchone()
    
    def math_tag_id(self,
                    inception_tag: str,
                    commit: bool = True) -> int:
        tag_id = self._get_tag_id(inception_tag)
        if not tag_id:
            tag_id = self._add_inception_tag(inception_tag, commit)
        return tag_id[0]

    def _add_tag_info(self,
                      tag_id: int,
                      tag_attrs: Iterable[MathtagAttrs],
                      commit: bool = True):
        for attr in tag_attrs:
            lang_id = self.lang_id(attr.lang, commit)
            self.conn.execute("""
            INSERT or IGNORE INTO math_tag_info (math_tag_id, info_type_id, lang_id, text)
            VALUES (
            :tag_id,
            (SELECT id FROM math_tag_info_types WHERE name = :attr_name),
            :lang_id,
            :text)""", vars(attr) | {'tag_id': tag_id, 'lang_id': lang_id})

        if commit:
            self.conn.commit()

    def add_nodes(self,
                  math_tags: Iterable[Mathtag]):
        with self.transaction():
            for tag in math_tags:
                tag_id = self.math_tag_id(tag.inception_id, commit=False)
                self._add_tag_info(tag_id, tag.attrs, commit=False)

    def _get_edge_type_id(self,
                          edge_type: str) -> Optional[Tuple[int, ]]:
        cur = self.conn.execute("""
        SELECT id
        FROM kb_edge_types
        WHERE name = (?)""", (edge_type, ))
        return cur.fetchone()

    def _add_edge_type(self,
                       edge_type: str,
                       commit: bool = True) -> Tuple[int, ]:
        if edge_type:
            cur = self.conn.execute("""
            INSERT INTO kb_edge_types (name)
            VALUES (?)
            RETURNING id""", (edge_type, ))
            if commit:
                self.conn.commit()
            edge_id = cur.fetchone()
        else:
            edge_id = [None]
        return edge_id

    def edge_type_id(self,
                     edge_type: str,
                     commit: bool = True) -> int:
        et_id = self._get_edge_type_id(edge_type)
        if not et_id:
            et_id = self._add_edge_type(edge_type, commit)
        if commit:
            self.conn.commit()
        return et_id[0]

    def add_edges(self,
                  math_tags: Iterable[Mathtag]):
        with self.transaction():
            for t in math_tags:
                e_type_id = self.edge_type_id(t.edge_type, commit=False)
                parent_id = self._get_tag_id(t.parent_id)
                if parent_id:
                    parent_id = parent_id[0]
                self.conn.execute("""
                UPDATE math_tags
                SET parent_id = (?),
                edge_type = (?)
                WHERE inception_id = (?)""", (parent_id, e_type_id, t.inception_id))

    def _get_annot_sent_id(self, annot_frag: AnnotFrag) -> int:
        cur = self.conn.execute("""
        SELECT sents.id
        FROM sents
        LEFT JOIN texts
        ON sents.text_id = texts.id
        WHERE sents.pos_in_text = :sent_idx
        AND texts.filename = :filename""", vars(annot_frag))
        return cur.fetchone()[0]

    def _get_annot_frag_id(self,
                           annot_sent_id: int,
                           annot_frag: AnnotFrag) -> Tuple[int, ]:
        cur = self.conn.execute('''
                SELECT annot_fragment.id
                FROM annot_fragment
                WHERE annot_fragment.sent_id = :db_sent_id
                AND annot_fragment.char_start = :char_start
                AND annot_fragment.char_end = :char_end''', vars(annot_frag) | {'db_sent_id': annot_sent_id})
        return cur.fetchone()

    def _add_annot_frag(self,
                        annot_sent_id: int,
                        annot_frag: AnnotFrag,
                        commit: bool = True) -> Tuple[int, ]:
        cur = self.conn.execute("""
        INSERT INTO annot_fragment (sent_id, char_start, char_end) 
        VALUES (:db_sent_id,
                :char_start,
                :char_end)
                RETURNING id""", vars(annot_frag) | {'db_sent_id': annot_sent_id})
        if commit:
            self.conn.commit()
        return cur.fetchone()

    def annot_frag_id(self,
                      annot_frag: AnnotFrag,
                      commit: bool = True) -> int:
        annot_sent_id = self._get_annot_sent_id(annot_frag)
        annot_frag_id = self._get_annot_frag_id(annot_sent_id, annot_frag)
        if not annot_frag_id:
            annot_frag_id = self._add_annot_frag(annot_sent_id, annot_frag, commit)
        return annot_frag_id[0]

    def _get_math_entity_id(self,
                            annot_frag_id: int,
                            math_ent: MathEntity) -> Tuple[int, ]:
        cur = self.conn.execute('''
        SELECT math_entities.id
        FROM math_entities
        WHERE math_entities.frag_id = :frag_id''', vars(math_ent) | {'frag_id' : annot_frag_id})

        return cur.fetchone()

    def _add_math_entity(self,
                         annot_frag_id: int,
                         math_ent: MathEntity,
                         commit: bool = True) -> Tuple[int, ]:
        tag_id = self._get_tag_id(math_ent.inception_id)[0]
        cur = self.conn.execute("""
        INSERT INTO math_entities (frag_id, math_tag_id, name) 
        VALUES (
        :frag_id, 
        :tag_id, 
        :name)
        RETURNING id""", {'frag_id': annot_frag_id, 'tag_id': tag_id, 'name': math_ent.name})

        if commit:
            self.conn.commit()
        return cur.fetchone()

    def math_entity_id(self, math_ent: MathEntity,
                       commit: bool = True) -> int:
        annot_frag_id = self.annot_frag_id(math_ent, commit=commit)
        math_ent_id = self._get_math_entity_id(annot_frag_id, math_ent)
        if not math_ent_id:
            math_ent_id = self._add_math_entity(annot_frag_id, math_ent, commit)
        return math_ent_id[0]

    def add_relations(self,
                      math_entity_id: int,
                      math_entity_related: Iterable[MathEntityRelated],
                      commit: bool = True):
        for rel in math_entity_related:
            frag_id = self.annot_frag_id(rel.fragment, commit=commit)
            self.conn.execute('''
            INSERT or IGNORE INTO math_annotation (annot_frag_id, math_ent_id, role_id) 
            VALUES (
            :frag_id, 
            :math_ent_id, 
            (SELECT id FROM math_roles WHERE role = :role))''', {
                'frag_id': frag_id,
                'math_ent_id': math_entity_id,
                'role': rel.role
            })
        if commit:
            self.conn.commit()

    def associate_tokens_and_annot(self, commit: bool = True):
        # TODO: кажется, здесь что-то не то происходит, потому что красится неправильно
        # TODO: исправить

        self.conn.execute('''
        DELETE FROM fragment_tokens''')

        self.conn.execute("""
        INSERT INTO fragment_tokens (token_id, frag_id)
        SELECT tokens.id AS token_id, annot_fragment.id AS frag_id
        FROM tokens
        JOIN annot_fragment ON tokens.sent_id = annot_fragment.sent_id
        WHERE tokens.char_start >= annot_fragment.char_start
        AND tokens.char_end <= annot_fragment.char_end""")

        if commit:
            self.conn.commit()

    def delete_dependent_math_ent_from_annot(self):
        self.conn.execute("""
        DELETE FROM math_annotation
        WHERE math_ent_id IN (
            SELECT math_entities.id
            FROM math_annotation
            LEFT JOIN math_roles
            ON math_roles.id = math_annotation.role_id
            LEFT JOIN math_entities
            ON math_entities.frag_id = math_annotation.annot_frag_id
            WHERE math_roles.role IN ('specifier', 'part')
            )""")
        self.conn.commit()

    def add_math_annotation(self, math_entity: MathEntity):
        with self.transaction():
            math_ent_id = self.math_entity_id(math_entity, commit=False)
            self.add_relations(math_ent_id, math_entity.related, commit=False)


class WebDBHandler(DBHandler):
    def get_sent_by_lemmatized_query(self,
                                     lemmatized_query: Iterable[str]) -> Iterable[dict]:
        pattern = '%' + '%'.join(lemmatized_query) + '%'
        cur = self.conn.execute('''
        SELECT sents.id, sents.lemmatized
        FROM sents
        WHERE sents.lemmatized LIKE ?''', (pattern,))
        cur.row_factory = self.dict_factory
        return cur.fetchall()

    def sent_info(self,
                  sent_id: int):
        cur = self.conn.execute('''
        SELECT sents.text_id, sents.pos_in_text, texts.youtube_link, sents.timecode
        FROM sents
        LEFT JOIN texts
        ON sents.text_id = texts.id
        WHERE sents.id = (?)         
        ''', (sent_id,))
        cur.row_factory = self.dict_factory
        return cur.fetchone()

    def sent_context(self,
                     text_id: int,
                     pos_in_text: int) -> Tuple[str, str]:
        cur = self.conn.execute('''
        SELECT sents.sent
        FROM sents
        WHERE text_id = :text_id
        AND (pos_in_text = :pos_in_text - 1)
        ''', {'text_id': text_id, 'pos_in_text': pos_in_text})
        cur.row_factory = self.one_column_factory
        left = cur.fetchone()
        cur = self.conn.execute(
            """
                SELECT sents.sent
                FROM sents
                WHERE text_id = :text_id
                AND (pos_in_text = :pos_in_text + 1)
                """,
            {"text_id": text_id, "pos_in_text": pos_in_text},
        )
        cur.row_factory = self.one_column_factory
        right = cur.fetchone()
        return left, right

    def sent_token_info(self,
                        sent_id: int) -> List[dict]:
        cur = self.conn.execute('''
        SELECT tokens.id, tokens.token, tokens.whitespace, pos.name AS 'pos', lemmas.name AS 'lemma', tokens.char_start, tokens.char_end
        FROM tokens
        LEFT JOIN lemmas
        ON lemmas.id = tokens.lemma_id
        LEFT JOIN pos
        ON pos.id = tokens.pos_id
        WHERE tokens.sent_id = (?)
        ORDER BY tokens.pos_in_sent
        ''', (sent_id,))
        cur.row_factory = self.dict_factory
        return cur.fetchall()

    def get_user_favourites(self,
                            userid: int):
        cur = self.conn.execute('''
        SELECT favourites.sent_id
        FROM favourites
        WHERE favourites.user_id = (?)
        ''', (userid,))
        cur.row_factory = self.one_column_factory
        return cur.fetchall()

    def get_pos_info(self):
        cur = self.conn.execute('''
        SELECT name, descr_rus, descr_eng, examples, UD_link
        FROM pos
        ORDER BY name''')
        return cur.fetchall()

    def get_available_tags(self, label_lang: str = "ui"):
        cur = self.conn.execute(
            """
        SELECT DISTINCT math_tags.inception_id, math_tag_info.text
        FROM math_tags
        LEFT JOIN math_entities
        ON math_entities.math_tag_id = math_tags.id
        JOIN math_tag_info
        ON math_tag_info.math_tag_id = math_tags.id
        JOIN langs
        ON langs.id = math_tag_info.lang_id
        WHERE math_entities.id NOTNULL
        AND langs.name = (?)""",
            (label_lang,),
        )
        cur.row_factory = self.dict_factory
    
        return cur.fetchall()

    
    def get_math_ontology(self):
        cur = self.conn.execute(
            """
        SELECT parent_id, id
        FROM math_tags"""
        )
        return cur.fetchall()
    
    def get_math_entities(self, math_tags: List[int]):
        # TODO: чтобы не находились те, которые зависимы от другой сущности (типа part или specifier)
        qmark_args = ", ".join("?" for t in math_tags)
    
        query = f"""
        SELECT math_entities.id
        FROM math_entities
        WHERE math_entities.math_tag_id IN ({qmark_args})"""
    
        cur = self.conn.execute(query, math_tags)
        cur.row_factory = self.one_column_factory
        return cur.fetchall()

    def get_html_math_annotation(self, math_ents: List[int]):
        qmark_args = ", ".join("?" for t in math_ents)
        query = f"""
        SELECT 
            annot_fragment.sent_id, 
            math_entities.id,
            GROUP_CONCAT(fragment_tokens.token_id) AS token_ids,
            GROUP_CONCAT(math_roles.color) AS colors,
            MIN(annot_fragment.char_start) AS min_char_start,
            MAX(annot_fragment.char_end) AS max_char_end,
            (MAX(annot_fragment.char_end) - MIN(annot_fragment.char_start)) AS char_range
        FROM fragment_tokens
        JOIN annot_fragment ON annot_fragment.id = fragment_tokens.frag_id
        JOIN math_annotation ON math_annotation.annot_frag_id = annot_fragment.id
        JOIN math_roles ON math_roles.id = math_annotation.role_id
        JOIN math_entities ON math_entities.id = math_annotation.math_ent_id
        WHERE math_entities.id IN ({qmark_args})
        GROUP BY math_entities.id, annot_fragment.sent_id
        ORDER BY annot_fragment.sent_id, min_char_start"""
    
        cur = self.conn.execute(query, math_ents)
        # cur.row_factory = self.dict_factory
        return cur.fetchall()
    
    def get_math_ent_sents(self, math_ents: List[int]):
        qmark_args = ", ".join("?" for t in math_ents)
        query = f"""
        SELECT DISTINCT annot_fragment.sent_id
        FROM math_entities
        JOIN annot_fragment
        ON annot_fragment.id = math_entities.frag_id
        WHERE math_entities.id IN ({qmark_args})"""
        cur = self.conn.execute(query, math_ents)
        cur.row_factory = self.one_column_factory
    
        return cur.fetchall()

    def math_tag_id(self, inception_id: str) -> int:
        cur = self.conn.execute(
            """
            SELECT id
            FROM math_tags
            WHERE inception_id = (?)""",
            (inception_id,),
        )

        return cur.fetchone()[0]
