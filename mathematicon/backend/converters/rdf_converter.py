import os
from typing import Union, Iterable, Dict, Tuple, List

from bs4 import BeautifulSoup
from bs4.element import Tag

from ..models.custom_dataclasses import Mathtag, MathtagAttrs
from ..models.database import MathDBHandler

BASE_PREFIX = "http://www.ukp.informatik.tu-darmstadt.de/inception/1.0#"


class RDFConverter:
    def __init__(self,
                 path: Union[os.PathLike, str],
                 base_prefix: str):
        self.base_prefix = base_prefix
        self.math_tags = self.parse_rdf(path)

    @staticmethod
    def _read_rdf(path: Union[os.PathLike, str]) -> BeautifulSoup:
        with open(path) as file:
            soup = BeautifulSoup(file, features="xml")
        return soup

    def _find_math_tags(self, tag: Tag):
        """
        Checks if an RDF tag represents a mathematical concept.

        Args:
            tag (Tag): The RDF tag to check.

        Returns:
            bool: True if the tag represents a mathematical concept within the base_prefix, False otherwise.
        """
        tag_id = tag.attrs.get("rdf:about", False)
        return tag.name == "Description" and tag_id and tag_id.startswith(self.base_prefix)

    def _get_tag_info(self, tag: Tag, inner_tags: List[str]) -> List[MathtagAttrs]:
        """
        Extracts information from specified inner tags of an RDF tag and returns a list of MathtagAttrs.

        Args:
            tag (Tag): The RDF tag containing inner tags.
            inner_tags (List[str]): A list of inner tag names to extract information from.

        Returns:
            List[MathtagAttrs]: A list of MathtagAttrs objects containing information about each inner tag.

        Notes:
            - If the xml:lang attribute is missing, 'unk' is used as the default language.

        Example:
            Given an RDF tag:

            <rdf:Description rdf:about="http://www.ukp.informatik.tu-darmstadt.de/inception/1.0#a7357b05d4f14e2cad12d6491fd6616b36">
                <rdf:type rdf:resource="http://www.w3.org/2002/07/owl#Class"/>
                <label xmlns="http://www.w3.org/2000/01/rdf-schema#" xml:lang="en">Logical predicate</label>
                <label xmlns="http://www.w3.org/2000/01/rdf-schema#" xml:lang="ru">Логический предикат</label>
                <comment xmlns="http://www.w3.org/2000/01/rdf-schema#" xml:lang="en">Returns truth value (0/1)</comment>
                <comment xmlns="http://www.w3.org/2000/01/rdf-schema#" xml:lang="ru">Возвращает значение истинности (0/1)</comment>
            </rdf:Description>

            Calling _get_tag_info(tag, ['label', 'comment']) would return a list with four MathtagAttrs objects:
            [
                MathtagAttrs(mathtag_id='a7357b05d4f14e2cad12d6491fd6616b36', attr_name='label', lang='en', text='Logical predicate'),
                MathtagAttrs(mathtag_id='a7357b05d4f14e2cad12d6491fd6616b36', attr_name='label', lang='ru', text='Логический предикат'),
                MathtagAttrs(mathtag_id='a7357b05d4f14e2cad12d6491fd6616b36', attr_name='comment', lang='en', text='Returns truth value (0/1)'),
                MathtagAttrs(mathtag_id='a7357b05d4f14e2cad12d6491fd6616b36', attr_name='comment', lang='ru', text='Возвращает значение истинности (0/1)')
            ]
        """
        infos = []
        inception_id = tag["rdf:about"].removeprefix(self.base_prefix)
        for tag_name in inner_tags:
            tag_elements = tag.find_all(tag_name)
            for el in tag_elements:
                try:
                    lang = el.attrs["xml:lang"]
                except KeyError:
                    lang = "unk"
                info = MathtagAttrs(
                    mathtag_id=inception_id, attr_name=tag_name, lang=lang, text=el.text
                )
                infos.append(info)
        return infos

    def _get_tag_parent(self, tag: Tag) -> Tuple[str, str]:
        """
        Retrieves the parent information of an RDF tag, including the parent identifier
        and the type of relationship (subClassOf or Instance).

        Args:
            tag (Tag): The RDF tag for which to retrieve parent information.

        Returns:
            Tuple[str, str]: A tuple containing the parent identifier and the edge type.
                - The parent identifier is a string representing the parent tag.
                - The edge type is a string indicating the type of relationship (subClassOf or Instance).

        Example:
            Given an RDF tag:

            <rdf:Description rdf:about="...">
                <subClassOf rdf:resource="base_prefix#parent_id"/>
            </rdf:Description>

            Calling get_tag_parent(tag) would return ('parent_id', 'subClassOf').

        Note:
            - If the tag has rdf:type but is not a subclass within the specified base_prefix,
              it is considered an Instance with parent 'root' and edge type 'Instance'.
        """
        subclass = tag.find("subClassOf")
        if subclass:
            parent = subclass.attrs["rdf:resource"].removeprefix(self.base_prefix)
            edge_type = "subClassOf"
        else:
            source = tag.find("rdf:type").attrs["rdf:resource"]
            if source.startswith(self.base_prefix):
                parent = source.removeprefix(self.base_prefix)
                edge_type = "Instance"
            else:
                parent = "root"
                edge_type = "Instance"
        return parent, edge_type

    def parse_rdf(self, path: Union[os.PathLike, str]) -> Iterable[Mathtag]:
        """
        Parses an RDF file located at the specified path and extracts mathematical concept information.

        Args:
            path (Union[os.PathLike, str]): The path to the RDF file.

        Returns:
            Iterable[Mathtag]: An iterable containing Mathtag objects representing mathematical concepts.

        Notes:
            - The first element in the iterable has 'root' as the inception_id, None as the parent_id and edge_type.
              It serves as the root or top-level concept in the hierarchy.

        Example:
            Given an RDF file with mathematical concepts:

            <rdf:Description rdf:about="http://www.ukp.informatik.tu-darmstadt.de/inception/1.0#a7357b05d4f14e2cad12d6491fd6616b36">
                <rdf:type rdf:resource="http://www.w3.org/2002/07/owl#Class"/>
                <label xmlns="http://www.w3.org/2000/01/rdf-schema#" xml:lang="en">Logical predicate</label>
                <label xmlns="http://www.w3.org/2000/01/rdf-schema#" xml:lang="ru">Логический предикат</label>
                <comment xmlns="http://www.w3.org/2000/01/rdf-schema#" xml:lang="en">Returns truth value (0/1)</comment>
                <comment xmlns="http://www.w3.org/2000/01/rdf-schema#" xml:lang="ru">Возвращает значение истинности (0/1)</comment>
            </rdf:Description>

            Calling parse_rdf(path) would return an iterable with Mathtag objects:
            [
                Mathtag(inception_id='root', parent_id=None, edge_type=None, attrs=[]),
                Mathtag(inception_id='a7357b05d4f14e2cad12d6491fd6616b36', parent_id='root', edge_type='Instance',
                        attrs=[
                            MathtagAttrs(mathtag_id='a7357b05d4f14e2cad12d6491fd6616b36', attr_name='label', lang='en', text='Logical predicate'),
                            MathtagAttrs(mathtag_id='a7357b05d4f14e2cad12d6491fd6616b36', attr_name='label', lang='ru', text='Логический предикат'),
                            MathtagAttrs(mathtag_id='a7357b05d4f14e2cad12d6491fd6616b36', attr_name='comment', lang='en', text='Returns truth value (0/1)'),
                            MathtagAttrs(mathtag_id='a7357b05d4f14e2cad12d6491fd6616b36', attr_name='comment', lang='ru', text='Возвращает значение истинности (0/1)')
                        ]
                )
            ]
        """
        soup = self._read_rdf(path)
        math_tags = [Mathtag(inception_id="root", parent_id=None, edge_type=None)]
        for el in soup.find_all(self._find_math_tags):
            inception_id = el["rdf:about"].removeprefix(self.base_prefix)
            tag_info = self._get_tag_info(el, ["label", "comment"])
            parent, edge_type = self._get_tag_parent(el)
            math_tag = Mathtag(inception_id, parent, edge_type, tag_info)
            math_tags.append(math_tag)
        return math_tags

    def to_database(self,
                    db: MathDBHandler):
        db.add_nodes(self.math_tags)
        db.add_edges(self.math_tags)


if __name__ == '__main__':
    from mathematicon.backend.models.database import MathDBHandler
    from mathematicon import DB_PATH

    rdf_path = input('Enter path to rdf file: ')
    rdf_converter = RDFConverter(rdf_path, BASE_PREFIX)

    db = MathDBHandler(DB_PATH)
    rdf_converter.to_database(db)

