from typing import List, Tuple
import logging

from ..repositories.lecture_repo import LectureRepository
from ..repositories.emebdding_repo import FormulaEmbeddingRepository
from ..repositories.annotation_repo import AnnotationRepository
from ..repositories.transcript_repo import TranscriptRepository
from ..model import FormulaAnnotation, AnnotationFragment
from ..converters.uima_cas_xmi_parser import UIMACASXMIParser


class FormulaAnnotationService:
    def __init__(self,
                 lecture_repo: LectureRepository,
                 transcript_repo: TranscriptRepository,
                 annotation_repo: AnnotationRepository,
                 formula_embeddings_repo: FormulaEmbeddingRepository,
                 ):
        self.embeddings_repo = formula_embeddings_repo
        self.annotation_repo = annotation_repo
        self.transcript_repo = transcript_repo
        self.lecture_repo = lecture_repo

    def load_formulas_annot_fragments(self, formulas: List[FormulaAnnotation]) -> List[AnnotationFragment]:
        fragments = []
        with self.annotation_repo:
            for formula in formulas:
                fragment = self.annotation_repo.get_annot_fragment_by_id(formula.fragment_id)
                fragment.annotation = formula
                fragments.append(fragment)
        return fragments

    @staticmethod
    def parse_from_xml(xml_path: str) -> List[AnnotationFragment]:
        parser = UIMACASXMIParser(xml_path)
        sents_offsets = parser.get_sents_offsets()

        annotation_fragments = []
        latex_annotations = parser.get_annotations("custom:LaTeX")
        for annot in latex_annotations:
            sent_id, annot_rel_offset = UIMACASXMIParser.sentence_relative_offsets(annot, sents_offsets)
            annot_fragment = AnnotationFragment(
                sentence_id=sent_id + 1,
                char_start=annot_rel_offset[0],
                char_end=annot_rel_offset[1],
            )
            annot_fragment.annotation = FormulaAnnotation(tex_formula=annot["formula"])
            annotation_fragments.append(annot_fragment)
        return annotation_fragments

    def add_formula_annotation(self, formula_annotation_fragment: AnnotationFragment):
        assert isinstance(formula_annotation_fragment.annotation, FormulaAnnotation), 'Formula annotation must be of type FormulaAnnotation'

        fragment = self.annotation_repo.add_annot_fragment(formula_annotation_fragment)
        formula = fragment.annotation
        formula.fragment_id = fragment.annotation_id
        try:
            self.embeddings_repo.add_formula(formula)
        except Exception as e:
            self._rollback_annotation_fragment(formula.fragment_id)
            logging.info('Failed to add formula annotation for formula %s', formula.tex_formula)

    def add_lecture_fragments(self, lecture_name: str, fragments: List[AnnotationFragment]) -> None:
        with self.lecture_repo:
            lecture_id = self.lecture_repo.get_lecture_id_from_filename(lecture_name)
        with self.transcript_repo:
            with self.annotation_repo:
                for fragment in fragments:
                    db_sentence_id = self.transcript_repo.get_sentence_id_by_pos_in_lecture(lecture_id, fragment.sentence_id)
                    fragment.sentence_id = db_sentence_id
                    self.add_formula_annotation(fragment)

    def _rollback_annotation_fragment(self, annotation_id: int):
        with self.annotation_repo:
            self.annotation_repo.delete_annot_fragment_by_id(annotation_id)

    def delete_formula_annot_fragment(self, annot_fragment: AnnotationFragment):
        assert getattr(annot_fragment, 'sentence_id', None) is not None
        with self.annotation_repo:
            if not annot_fragment.annotation_id:
                annot_fragment_id = self.annotation_repo.get_annot_frag_id(annot_fragment)
                annot_fragment.annotation_id = annot_fragment_id
            annot_fragment.annotation.fragment_id = annot_fragment.annotation_id
            self.embeddings_repo.delete_formula(annot_fragment.annotation)
            self.annotation_repo.conditional_delete_annot_fragment_by_id(annot_fragment.annotation_id)


if __name__ == '__main__':
    import logging
    from TangentCFT.tangent_cft.tangent_cft_back_end import TangentCFTBackEnd
    from TangentCFT.tangent_cft.embedding_function import TangentCFTEmbedding

    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.DEBUG)

    xml_example = '/Users/viktoriaknazkova/Downloads/bezbotvy_naititochkirazryvafunktsiineprerivnost (3)/bezbotvy_naititochkirazryvafunktsiineprerivnost.xmi'
    annotations = FormulaAnnotationService.parse_from_xml(xml_example)
    # print(annotations)

    db_path = '/Users/viktoriaknazkova/Desktop/me/study/github_repos/mathematicon_mathIR/data/mathematicon.db'
    chroma_db_path = '/Users/viktoriaknazkova/Desktop/me/study/github_repos/mathematicon_mathIR/data'

    lecture_repo = LectureRepository(db_path)
    transcript_repo = TranscriptRepository(db_path)
    annotation_repo = AnnotationRepository(db_path)

    tangent_cft = TangentCFTBackEnd.load(encoder_map_path='/Users/viktoriaknazkova/Desktop/me/study/github_repos/TangentCFT/Models/Vocabulary/opt_encoder.tsv',
                                         ft_model_path='/Users/viktoriaknazkova/Desktop/me/study/github_repos/TangentCFT/Models/FastText/opt_model.model')
    embedder = TangentCFTEmbedding(tangent_cft=tangent_cft, mathml=False, slt=False)
    formula_embeddings_repo = FormulaEmbeddingRepository(chroma_db_path, emb_function=embedder)

    formula_annotation_service = FormulaAnnotationService(lecture_repo, transcript_repo, annotation_repo, formula_embeddings_repo)

    from pathlib import Path
    lecture_fname = Path(xml_example).stem
    formula_annotation_service.add_lecture_fragments(lecture_fname, annotations)
