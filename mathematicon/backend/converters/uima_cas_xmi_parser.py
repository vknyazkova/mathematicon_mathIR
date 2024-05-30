import os
from typing import Union, Tuple, List, Dict
from bisect import bisect_left, bisect_right

from bs4 import BeautifulSoup
import html


class UIMACASXMIParser:
    def __init__(self,
                 xmi_file: Union[str, os.PathLike]):
        with open(xmi_file) as file:
            self.soup = BeautifulSoup(file, features="xml")

    def get_text(self) -> str:
        return self.soup.find("cas:Sofa").attrs["sofaString"]

    def get_sents_offsets(self) -> Tuple[List[int], List[int]]:
        found_sents = sorted(
            self.get_annotations("type5:Sentence"), key=lambda entity: int(entity.get("id"))
        )
        begin, end = [], []
        for sent in found_sents:
            begin.append(int(sent["begin"]))
            end.append(int(sent["end"]))
        return begin, end

    def get_annotations(self, tagname: str) -> List[Dict[str, str]]:
        annotations = []
        for el in self.soup.find_all(tagname):
            attrs = {key: html.unescape(value) for key, value in el.attrs.items()}
            annotations.append(attrs)
        return annotations

    @staticmethod
    def sentence_relative_offsets(annotation: Dict[str, str],
                                  sentes_offsets: Tuple[List[int], List[int]]) -> Tuple[int, Tuple[int, int]]:
        annotation_offset = int(annotation['begin']), int(annotation['end'])
        begin_sent_idx = bisect_right(sentes_offsets[0], annotation_offset[0])
        end_sent_idx = bisect_left(sentes_offsets[1], annotation_offset[1])
        assert begin_sent_idx - 1 == end_sent_idx, "Annotation is out of sentence bounds"
        relative_offset = (
            annotation_offset[0] - sentes_offsets[0][end_sent_idx],
            annotation_offset[1] - sentes_offsets[0][end_sent_idx]
        )
        return end_sent_idx, relative_offset
