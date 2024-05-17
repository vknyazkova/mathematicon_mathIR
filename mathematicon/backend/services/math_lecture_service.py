from ..repositories.lecture_repo import LectureRepository
from ..model import MathLecture


class MathLectureService:
    def __init__(self,
                 lecture_repo: LectureRepository):
        self.lecture_repo = lecture_repo

    def add_lecture(self, lecture: MathLecture) -> MathLecture:
        return self.lecture_repo.add_lecture(lecture)