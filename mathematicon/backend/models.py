from typing import Optional, List

from sqlmodel import Field, Relationship, SQLModel, create_engine


class Text(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    filename: str = Field(unique=True)
    youtube_link: str
    timecode_start: str
    timecode_end: str
    math_branch: str
    difficulty: str

    # sents: List["Sentence"] = Relationship(back_populates="sentence")

#
# class Sentence(SQLModel, table=True):
#     id: Optional[int] = Field(default=None, primary_key=True)
#     text: str
#     lemmatized: str
#     pos_in_text: int
#     timecode: str
#
#     text_id: Optional[int] = Field(default=None, foreign_key="text.id")
#     text: Optional[Text] = Relationship(back_populates="text")
#
#
# class MorphFeature(SQLModel, table=True):
#     __tablename__ = "morph_feature"
#     id: Optional[int] = Field(default=None, primary_key=True)
#     category: str
#     value: str
#
#
# class Lemma(SQLModel, table=True):
#     id: Optional[int] = Field(default=None, primary_key=True)
#     value: str
#
#
# class POS(SQLModel, table=True):
#     id: Optional[int] = Field(default=None, primary_key=True)
#     name: str
#     descr_rus: Optional[str] = None
#     descr_en: Optional[str] = None
#     examples: Optional[str] = None
#     ud_link: Optional[str] = None
#
#
# class TokenMorphFeatures(SQLModel, table=True):
#     __tablename__ = "token_morph_features"
#     token_id: Optional[int] = Field(default=None, foreign_key="token.id", primary_key=True)
#     feature_id: Optional[int] = Field(default=None, foreign_key="morph_feature.id", primary_key=True)
#
#
# class Token(SQLModel, table=True):
#     id: Optional[int] = Field(default=None, primary_key=True)
#     token: str
#     whitespace: bool
#     offset_start: int
#     offset_end: int
#
#     sent_id: Optional[int] = Field(default=None, foreign_key="sentence.id")
#     lemma_id: Optional[int] = Field(default=None, foreign_key="lemma.id")
#     morph_features: List[MorphFeature] = Relationship(back_populates="morph_feature", link_model=TokenMorphFeatures)


if __name__ == '__main__':
    sqlite_file_name = "database.db"
    sqlite_url = f"sqlite:///{sqlite_file_name}"

    engine = create_engine(sqlite_url, echo=True)
    # SQLModel.metadata.create_all(engine)
    text1 = Text(title='Формула Бернулли',
                 filename='danillebedev_formulabernyli',
                 youtube_link='https://youtu.be/ysZ3ggU-bLQ',
                 math_branch='статистика',
                 difficulty='школьная программа',
                 timecode_start='0:00',
                 timecode_end='7:50'
                 )


