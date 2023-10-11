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


@dataclass
class HTMLsentence:
    tokens: List[HTMLSpan] = field(default_factory=list)
    left: str = ''
    right: str = ''
    yb_link: str = ''
    star: bool = False


@dataclass
class QueryInfo:
    tokens: List[HTMLSpan] = field(default_factory=list)
    pos_string: str = ''
    lemmatized: str = ''
    formula: List[str] = None