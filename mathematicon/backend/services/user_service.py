import os
from typing import List, Tuple

from hashlib import pbkdf2_hmac

from ..repositories.user_repo import UserRepository
from ..repositories.transcript_repo import TranscriptRepository
from ..model import UserInfo, SearchHistory, Favorites
from ..models.html_models import HTMLSentence, HTMLFavorites


N_ITERS = 500


class UserService:
    def __init__(self,
                 user_repository: UserRepository,
                 transcript_repository: TranscriptRepository):
        self.user_repo = user_repository
        self.transcript_repo = transcript_repository

    @staticmethod
    def validate_password(user: UserInfo,
                          entered: str) -> bool:
        entered_hash, _ = UserService.generate_password_hash(entered, salt=user.salt)
        if entered_hash == user.password_hash:
            return True
        else:
            return False

    @staticmethod
    def generate_password_hash(password: str,
                               salt: bytes = None) -> Tuple[str, bytes]:
        if not salt:
            salt = os.urandom(12)
        password = bytes(password, encoding='utf8')
        dk = pbkdf2_hmac('sha256', password, salt, N_ITERS)
        return dk.hex(), salt

    def create_user(self,
                    username: str,
                    password: str,
                    email: str) -> UserInfo:
        with self.user_repo:
            password_hash, salt = self.generate_password_hash(password)
            user = UserInfo(
                username=username,
                email=email,
                password_hash=password_hash,
                salt=salt)
            return self.user_repo.add_user(user)

    def get_by_username(self,
                        username: str) -> UserInfo:
        with self.user_repo:
            return self.user_repo.get_by_username(username)

    def save_history(self,
                     history: SearchHistory):
        with self.user_repo:
            self.user_repo.update_history(history)

    def add_favorites(self, favorites: Favorites):
        with self.user_repo:
            self.user_repo.add_favorites(favorites)

    def remove_favorites(self, favorites: Favorites):
        with self.user_repo:
            self.user_repo.remove_favorites(favorites)

    def get_user_search_history(self, user: UserInfo) -> List[SearchHistory]:
        with self.user_repo:
            return self.user_repo.get_user_search_history(user)

    def get_user_favorites(self, user: UserInfo) -> List[HTMLFavorites]:
        with self.user_repo:
            favorites = self.user_repo.get_user_favorites(user)

        with self.transcript_repo:
            html_favorites = {}
            for favorite in favorites:
                sentence = self.transcript_repo.get_sentence_by_id(favorite.sentence_id)
                if favorite.query not in html_favorites:
                    html_favorites[favorite.query] = HTMLFavorites(
                        query_text=favorite.query,
                        query_link=favorite.link
                    )
                html_favorites[favorite.query].sentences.append((sentence.sentence_id, sentence.sentence_text))
        return list(html_favorites.values())

    def personalise_search_results(self,
                                   user: UserInfo,
                                   search_results: List[HTMLSentence]) -> List[HTMLSentence]:
        with self.user_repo:
            favorites = self.user_repo.get_user_favorites(user)
        fav_sents = set([f.sentence_id for f in favorites])
        fav_sorted = sorted(
                search_results, key=lambda x: 1 if x.id in fav_sents else 0, reverse=True
            )
        for sent in fav_sorted:
            if sent.id not in fav_sents:
                break
            sent.star = "true"
        return fav_sorted


