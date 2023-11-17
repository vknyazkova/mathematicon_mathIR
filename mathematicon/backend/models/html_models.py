from dataclasses import dataclass, field
from typing import List


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
    char_start_: int = None
    char_end_: int = None


@dataclass
class HTMLsentence:
    id: int
    tokens: List[HTMLSpan] = field(default_factory=list)
    left: str = ''
    right: str = ''
    yb_link: str = ''
    star: bool = False


@dataclass
class QueryInfo:
    tokens: List[HTMLWord] = field(default_factory=list)
    formula: List[str] = None
