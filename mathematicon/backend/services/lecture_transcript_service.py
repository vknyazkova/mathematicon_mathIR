import os
from typing import List, Optional, Union, Tuple

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
                         text_id: Optional[int] = None,
                         save_to_conllu: Optional[Union[str, os.PathLike]] = None) -> List[Sentence]:

        if 'conllu_formatter' not in [pipe[0] for pipe in self.nlp.pipeline]:
            self.nlp.add_pipe("conll_formatter", last=True, config={'include_headers': True})
        doc = self.nlp(transcript)
        if save_to_conllu is not None:
            with open(save_to_conllu, "w", encoding="utf-8") as f:
                f.write(doc._.conll_str)
                
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
        with self.transcript_repo:
            self.transcript_repo.add_transcript(sentences)

    def get_sentence_context(self, sentence: Sentence) -> Tuple[Optional[str], Optional[str]]:
        with self.transcript_repo:
            return self.transcript_repo.sentence_context(sentence)

    def get_sentence_yb_link(self, sentence: Sentence) -> str:
        with self.transcript_repo:
            return self.transcript_repo.get_sentence_yb_link(sentence)

    def exact_match_search(self, text: str) -> List[Sentence]:
        with self.transcript_repo:
            return self.transcript_repo.search_phrase(text)

    def lemmatized_search(self, lemmatized_query: List[str]) -> List[Sentence]:
        with self.transcript_repo:
            return self.transcript_repo.search_lemmatized(lemmatized_query)


if __name__ == '__main__':
    import spacy

    nlp = spacy.load("ru_core_news_sm", exclude=["ner"])
    doc = nlp('Пришла на кухню')
    print(str(doc[0].morph))
