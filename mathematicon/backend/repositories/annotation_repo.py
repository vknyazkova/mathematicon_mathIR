from ..model import AnnotationFragment


class AnnotationRepository:
    def __init__(self):
        ...

    def add_annot_fragment(self, annot_fragment: AnnotationFragment) -> AnnotationFragment:
        ...

    def get_annot_fragment_by_id(self, annot_fragment_id: id) -> AnnotationFragment:
        ...