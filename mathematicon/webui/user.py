import flask_login

from ..backend.model import UserInfo


class User(flask_login.UserMixin):
    def __init__(self, user_info: UserInfo):
        self.user_info = user_info

    @property
    def id(self):
        return self.user_info.username

    @property
    def username(self):
        return self.user_info.username

    @property
    def email(self):
        return self.user_info.email

    def is_authenticated(self) -> bool:
        return True

    def is_active(self) -> bool:
        return True

    def is_anonymous(self) -> bool:
        return False

    def get_id(self) -> str:
        return self.user_info.username
