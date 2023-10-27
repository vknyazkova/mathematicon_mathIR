from hashlib import pbkdf2_hmac
import os
from typing import Union, Tuple

import flask_login

from ..backend.models.database import UserDBHandler

N_ITERS = 500


class User(flask_login.UserMixin, UserDBHandler):

    def __init__(self,
                 db_path: Union[str, os.PathLike]):
        UserDBHandler.__init__(self, db_path)
        self.email = None
        self.salt = None
        self.password = None
        self.id = None
        self.username = None

    def __repr__(self):
        return f'User {self.username}'

    def is_authenticated(self) -> bool:
        return True

    def is_active(self) -> bool:
        return True

    def is_anonymous(self) -> bool:
        return False

    def get_id(self) -> str:
        return str(self.username)

    @staticmethod
    def hash_password(password: str,
                      salt: bytes = None) -> Tuple[str, bytes]:
        if not salt:
            salt = os.urandom(12)
        password = bytes(password, encoding='utf8')
        dk = pbkdf2_hmac('sha256', password, salt, N_ITERS)
        return dk.hex(), salt

    def validate_password(self,
                          entered: str) -> bool:
        entered_hash, _ = User.hash_password(entered, salt=self.salt)
        if entered_hash == self.password:
            return True
        else:
            return False

    def get(self,
            username: str):
        res = self.get_user_by_uname(username)
        if res:
            for key in res:
                setattr(self, key, res[key])
            return self
        else:
            return None

