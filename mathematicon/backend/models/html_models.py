from dataclasses import dataclass, field
from typing import List, Union, Tuple


@dataclass
class HTMLSpan:
    text: str
    html_type: str = 'plain'
    color: str = 'black'


@dataclass
class HTMLWord(HTMLSpan):
    html_type: str = 'tooltip'
    pos: str = None
    lemma: str = None


@dataclass
class HTMLAnnotated:
    annotation: str
    html_type: str = 'annotation'
    spans: List[HTMLSpan] = field(default_factory=list)


@dataclass
class HTMLSentence:
    id: int
    tokens: List[Union[HTMLSpan, HTMLAnnotated]] = field(default_factory=list)
    left: str = ''
    right: str = ''
    yb_link: str = ''
    star: str = "false"


@dataclass
class QueryInfo:
    tokens: List[HTMLWord] = field(default_factory=list)
    formula: List[str] = None


@dataclass
class HTMLFavorites:
    query_text: str
    query_link: str
    sentences: List[Tuple[int, str]] = field(default_factory=list)
