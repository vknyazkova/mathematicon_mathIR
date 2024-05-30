from ..repositories.lecture_repo import LectureRepository
from ..model import MathLecture


class MathLectureService:
    def __init__(self,
                 lecture_repo: LectureRepository):
        self.lecture_repo = lecture_repo

    def add_lecture(self, lecture: MathLecture) -> MathLecture:
        with self.lecture_repo:
            return self.lecture_repo.add_lecture(lecture)