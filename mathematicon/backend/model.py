from pydantic import BaseModel, Field
from typing import List, Optional


class MathLecture(BaseModel):
    lecture_id: Optional[int] = Field(None, description='Lecture ID in database')
    youtube_link: str
    timecode_start: str
    timecode_end: str
    filename: str
    title: str
    difficulty_level: str
    math_branch: str


class Token(BaseModel):
    token_id: Optional[int] = Field(None, description='Token ID in database')
    sentence_id: Optional[int] = Field(None, description='Sentence ID in database')
    token_text: str
    whitespace: bool
    pos_tag: str
    lemma: str
    morph_annotation: str
    position_in_sentence: int
    char_offset_start: int
    char_offset_end: int



class Sentence(BaseModel):
    sentence_id: Optional[int] = Field(None, description='Sentence ID in database')
    lecture_id: Optional[int] = Field(None, description="Lecture ID in database")
    position_in_text: int
    sentence_text: str
    lemmatized_sentence: str
    timecode_start: Optional[str]

    tokens: List[Token] = Field(default_factory=list)
