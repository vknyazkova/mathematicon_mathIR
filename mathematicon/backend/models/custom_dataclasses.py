from dataclasses import dataclass, field
from typing import List
from spacy.tokens import Span, Token, Doc


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


class DatabaseToken:
    def __init__(self,
                 spacy_token: Token,
                 pos_in_text: int,
                 char_start: int,
                 char_end: int,
                 filename: str,
                 sent_pos_in_text: int):
        self.token = spacy_token.text
        self.whitespace = 1 if spacy_token.whitespace_ else 0
        self.lemma = spacy_token.lemma_
        self.pos = spacy_token.pos_

        self.pos_in_text = pos_in_text
        self.char_start = char_start
        self.char_end = char_end
        self.filename = filename
        self.sent_pos_in_text = sent_pos_in_text


class DatabaseText:
    def __init__(self,
                 sentences: Doc,
                 filename: str,
                 title: str,
                 yb_link: str,
                 branch: str,
                 level: str):
        self._sentences = sentences

        self.filename = filename
        self.title = title
        self.yb_link = yb_link
        self.branch = branch
        self.level = level

    def __iter__(self):
        for i, sent in enumerate(self._sentences.sents, start=1):
            sentence = DatabaseSentence(
                spacy_span=sent,
                pos_in_text=i,
                filename=self.filename
            )
            yield sentence

    def dict_(self):
        return {k: v for k, v in vars(self).items() if not k.startswith('_')}


class DatabaseSentence:
    def __init__(self,
                 spacy_span: Span,
                 pos_in_text: int,
                 filename: str):
        self._sent = spacy_span

        self.sent_text = spacy_span.text
        self.lemmatized = ' '.join((t.lemma_ for t in spacy_span))
        self.pos_in_text = pos_in_text
        self.filename = filename

    def tokens_attr(self, attr_name: str, out_style: str = 'tuple'):
        """
        Yields attribute value of attr_name for every token in the sentence
        Args:
            attr_name: attribute name to retrieve value
            out_style: how to return value
                'tuple': returns tuple (attr_val,)  (useful for qmark placeholder style)
                'val': returns value only
                'dict': returns dict {attr_name: attr_val} (useful for named placeholders)

        Returns: attribute value in out_style

        """
        for t in self._sent:
            attr_val = getattr(t, attr_name)
            if out_style == 'tuple':
                yield (attr_val,)
            elif out_style == 'val':
                yield attr_val
            elif out_style == 'dict':
                yield {attr_name, attr_val}

    def token_info_generator(self):
        char_cur = 0
        for i, t in enumerate(self._sent, start=1):
            char_end = char_cur + len(t.text)
            token = DatabaseToken(spacy_token=t,
                                  pos_in_text=i,
                                  char_start=char_cur,
                                  char_end=char_end + 1,
                                  filename=self.filename,
                                  sent_pos_in_text=self.pos_in_text)
            yield token
            char_cur = char_end + len(t.whitespace_)

    def dict_(self):
        return {k: v for k, v in vars(self).items() if not k.startswith('_')}
