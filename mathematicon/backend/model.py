from pydantic import BaseModel, Field
from typing import List, Optional, Sequence, Union


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
    morph_annotation: Optional[str]
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


class FormulaAnnotation(BaseModel):
    fragment_id: Optional[int] = Field(None, description='Annotation fragment ID in database')
    tex_formula: str
    embedding_vector: Optional[Sequence[float]]


class AnnotationFragment(BaseModel):
    annotation_id: Optional[int] = Field(None, description='Annotation ID in database')
    sentence_id: int
    char_start: int
    char_end: int

    token_ids: List[int] = Field(default_factory=list)
    annotation: Optional[Union[FormulaAnnotation, str]]


class UserInfo(BaseModel):
    user_id: Optional[int] = Field(None, description='User ID in database')
    username: str
    email: str
    password_hash: str
    salt: bytes


class SearchHistory(BaseModel):
    search_id: Optional[int] = Field(None, description='Search ID in database')
    user_id: int
    timestamp: str
    query: str
    link: str


class Favorites(BaseModel):
    favorite_id: Optional[int] = Field(None, description='Favorite ID in database')
    user_id: int
    query: str
    link: Optional[str]
    sentence_id: int