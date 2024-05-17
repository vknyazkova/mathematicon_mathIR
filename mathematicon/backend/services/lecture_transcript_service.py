from typing import List, Optional

from spacy import Language

from ..repositories.transcript_repo import TranscriptRepository
from ..model import Sentence, Token


class LectureTranscriptService:
    def __init__(self,
                 transcript_repo: TranscriptRepository,
                 nlp: Language):
        self.transcript_repo = transcript_repo
        self.nlp = nlp

    def parse_transcript(self,
                         transcript: str,
                         text_id: Optional[int] = None) -> List[Sentence]:
        doc = self.nlp(transcript)
        sentences = []
        for i, sent in enumerate(doc.sents):
            lemmas = []
            tokens = []
            char_count = 0
            for j, token in enumerate(sent):
                lemmas.append(token.lemma_)
                tokens.append(
                    Token(
                        token_text=token.text,
                        whitespace=True if token.whitespace_ else False,
                        pos_tag=token.pos_,
                        lemma=token.lemma,
                        morph_annotation=str(token.morph),
                        position_in_sentence=j,
                        char_offset_start=char_count,
                        char_offset_end=char_count + len(token.text),
                    )
                )
                char_count += len(token.text) + len(token.whitespace_)
            sentences.append(
                Sentence(
                    lecture_id=text_id,
                    position_in_text=i,
                    sentence_text=sent.text,
                    lemmatized_sentence=' '.join([lemma for lemma in lemmas]),
                    tokens=tokens
                )
            )
        return sentences

    def add_transcript(self,
                       transcript: str,
                       text_id: int):
        sentences = self.parse_transcript(transcript, text_id)
        self.transcript_repo.add_transcript(sentences)


if __name__ == '__main__':
    import spacy

    nlp = spacy.load("ru_core_news_sm", exclude=["ner"])
    doc = nlp('Пришла на кухню')
    print(str(doc[0].morph))
