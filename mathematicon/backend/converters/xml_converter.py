import os
from bisect import bisect_left
from typing import Iterable, Union, Tuple, List, Dict
from pathlib import Path

from bs4 import BeautifulSoup
from bs4.element import Tag

from ..models.db_data_models import XMISents, MathEntity, AnnotFrag, MathEntityRelated
from ..models.database import MathDBHandler

BASE_PREFIX = "http://www.ukp.informatik.tu-darmstadt.de/inception/1.0#"
MATH_ENTITY_LAYER = "custom:Math_entities"
LINK_FEATURES = ("args", "subpart")


class XMLConverter:
    """
    Converts XML annotations to an intermediate data structure for database use.

    Attributes:
        MATH_ENTITY_ROLE (str): role name for math entity itself
    """

    MATH_ENTITY_ROLE = "math_entity"

    def __init__(self,
                 base_prefix: str,
                 math_entity_layer: str,
                 math_ent_link_features: Iterable[str]):
        self.base_prefix = base_prefix
        self.math_entity_layer = math_entity_layer
        self.link_features = math_ent_link_features

        self.filename = None
        self.soup = None
        self.sents: XMISents = None

        self.math_entities: Iterable[MathEntity] = None

    @staticmethod
    def _load_xml(filepath: Union[str, os.PathLike]) -> Tuple[str, BeautifulSoup]:
        """
        Loads XML from a file and returns the filename and BeautifulSoup object.

        Args:
            filepath (Union[str, Path]): Path to the XML file.

        Returns:
            Tuple[str, BeautifulSoup]: Filename and BeautifulSoup object.
        """
        path = Path(filepath).resolve()
        with open(path) as file:
            soup = BeautifulSoup(file, features="xml")
        return path.stem, soup

    def _get_sents_info(self) -> XMISents:
        """
        Extracts sentence information from the XML.

        Returns:
            XMISents: Sentence information.
        """
        text = self.soup.find("cas:Sofa").attrs["sofaString"]
        sents = XMISents()
        found_sents = sorted(
            self.soup.find_all("type5:Sentence"), key=lambda entity: int(entity.get("id"))
        )
        for sent in found_sents:
            offset = int(sent.attrs["begin"]), int(sent.attrs["end"])
            sents.begin.append(offset[0])
            sents.end.append(offset[1])
            sents.text.append(text[offset[0]: offset[1]])
        return sents

    def _get_sentence_index(self, annot_offset: Tuple[int, int]):
        """
        Determines the sentence index based on the annotation offset.

        Args:
            annot_offset (Tuple[int, int]): A tuple representing the start and end offsets
            of an annotation within the document.

        Returns:
            int: The index of the sentence to which the annotation belongs.

        Example:
            Suppose we have a document with the following sentence boundaries:
            Sentences: ["This is sentence 1.", "And this is sentence 2."]

            If the annotation offset is (32, 42), which corresponds to the text "sentence 2",
            the function will return 1, indicating that the annotation is part of the second sentence
            (assuming 0-based indexing).
        """
        begin_sent_idx = bisect_left(self.sents.end, annot_offset[0])
        end_sent_idx = bisect_left(self.sents.end, annot_offset[1])
        assert begin_sent_idx == end_sent_idx
        return begin_sent_idx

    @staticmethod
    def _calculate_relative_offset(annot_offset: Tuple[int, int], sent_char_start: int) -> Tuple[int, int]:
        """
        Calculates the relative offset within a sentence.

        Args:
            annot_offset (Tuple[int, int]): Annotation offset.
            sent_char_start (int): Character start of the sentence.

        Returns:
            Tuple[int, int]: Relative offset.
        """
        return (
            annot_offset[0] - sent_char_start,
            annot_offset[1] - sent_char_start
        )

    def _get_inception_id(self, math_entity_tag: Tag) -> str:
        """
        Gets the inception ID from the math entity tag.

        Args:
            math_entity_tag: Math entity tag.

        Returns:
            str: Inception ID.
        """
        math_tag = math_entity_tag.attrs.get("math_tag", None)
        if math_tag:
            math_tag = math_tag.removeprefix(self.base_prefix)
        return math_tag

    def _get_link_target_fragment(self, link_xmi_id: str) -> MathEntityRelated:
        """
        Gets the target fragment based on the link ID.

        Args:
            link_xmi_id: XMI ID of the link.

        Returns:
            MathEntityRelated: Target fragment and its role.
        """
        link_tag = self.soup.find(attrs={"xmi:id": link_xmi_id})
        target_tag = self.soup.find(attrs={"xmi:id": link_tag.attrs["target"]})
        annotation = self._annot_fragment_info(target_tag)
        role = link_tag.attrs.get('role', None)
        return MathEntityRelated(fragment=annotation, role=role)

    def _math_entity_related_tags(self, math_ent_tag: Tag) -> Iterable[MathEntityRelated]:
        """
        Extracts related tags for a math entity.

        Args:
            math_ent_tag: Math entity tag.

        Returns:
            Iterable[MathEntityRelated]: List of related tags.
        """
        related = [MathEntityRelated(self._annot_fragment_info(math_ent_tag), role=XMLConverter.MATH_ENTITY_ROLE)]
        for attr_name in self.link_features:
            attr_value = math_ent_tag.attrs.get(attr_name, None)
            if attr_value:
                related_tags = attr_value.split(' ')
                related.extend((self._get_link_target_fragment(t) for t in related_tags))
        return related

    def _annot_fragment_info(self, ent_tag: Tag) -> AnnotFrag:
        """
        Extracts annotation fragment information from a tag.

        Args:
            ent_tag: XML tag representing an annotation fragment.

        Returns:
            AnnotFrag: Annotation fragment information.
        """

        ent_offset = int(ent_tag.attrs["begin"]), int(ent_tag.attrs["end"])
        ent_sent_idx = self._get_sentence_index(ent_offset)
        relative_ent_offset = self._calculate_relative_offset(
            ent_offset, self.sents.begin[ent_sent_idx]
        )
        fragment = AnnotFrag(self.filename, ent_sent_idx + 1, *relative_ent_offset)
        return fragment

    def _extract_math_entity_info(self, math_ent_tag) -> MathEntity:
        """
        Extracts information from a math entity tag and creates a MathEntity object.

        Args:
           math_ent_tag: Math entity tag.

        Returns:
           MathEntity: Extracted information as a MathEntity object.
        """
        annot_fragment = self._annot_fragment_info(math_ent_tag)

        math_entity = MathEntity(
            **vars(annot_fragment),
            inception_id=self._get_inception_id(math_ent_tag),
            name=math_ent_tag.attrs.get('Name', None),
            related=self._math_entity_related_tags(math_ent_tag)
        )
        return math_entity

    def get_math_entities(self) -> Iterable[MathEntity]:
        """
        Extracts math entities from the XML.

        Returns:
            Iterable[MathEntity]: List of math entities.
        """
        math_entities = []
        for math_ent_tag in self.soup.find_all(self.math_entity_layer):
            math_entity = self._extract_math_entity_info(math_ent_tag)
            math_entities.append(math_entity)
        return math_entities

    def pprint_math_entities(self):
        for math_ent in self.math_entities:
            print(math_ent.inception_id)
            fragments = []
            roles = []
            for ent in sorted(math_ent.related, key=lambda x: x.fragment.char_start):
                ent_text = self.sents.text[ent.fragment.sent_idx - 1][ent.fragment.char_start: ent.fragment.char_end]
                fragments.append(ent_text)
                roles.append(ent.role)
            print(*fragments, sep='\t')
            print(*roles, sep='\t')
            print()

    def parse_annotation(self,
                         filepath: Union[str, os.PathLike]):
        """
        Parses XML annotation from a file.

        Args:
           filepath (Union[str, Path]): Path to the XML file.
        """
        self.filename, self.soup = self._load_xml(filepath)
        self.sents = self._get_sents_info()
        self.math_entities = self.get_math_entities()

    def to_database(self,
                    db: MathDBHandler):
        for math_ent in self.math_entities:
            db.add_math_annotation(math_ent)
        db.delete_dependent_math_ent_from_annot()
        db.associate_tokens_and_annot()


if __name__ == '__main__':
    xml_conv = XMLConverter(BASE_PREFIX, MATH_ENTITY_LAYER, LINK_FEATURES)
    filepath = input('Enter path to annotation file: ')
    xml_conv.parse_annotation(filepath)
    # xml_conv.pprint_math_entities()

    from mathematicon import DB_PATH
    db = MathDBHandler(DB_PATH)
    xml_conv.to_database(db)



