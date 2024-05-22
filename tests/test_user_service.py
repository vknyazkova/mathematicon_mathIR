import unittest
from unittest.mock import MagicMock

from mathematicon.backend.model import UserInfo, Favorites, Sentence
from mathematicon.backend.repositories.user_repo import UserRepository
from mathematicon.backend.repositories.transcript_repo import TranscriptRepository
from mathematicon.backend.services.user_service import UserService
from mathematicon.backend.models.html_models import HTMLSentence, HTMLFavorites


class TestUserService(unittest.TestCase):
    def setUp(self):
        mock_user_repo = MagicMock(spec=UserRepository)
        mock_transcript_repo = MagicMock(spec=TranscriptRepository)
        self.user_service = UserService(mock_user_repo, mock_transcript_repo)

    def test_personalise_search_results(self):
        user_info = UserInfo(
            user_id=1, username='user1', email='sample@gmail.com',
            password_hash='fnd28fhn3', salt='salt'.encode()
        )
        search_results = [
            HTMLSentence(id=1),
            HTMLSentence(id=2),
            HTMLSentence(id=3),
            HTMLSentence(id=4),
            HTMLSentence(id=5),
        ]
        user_favorites = [
            Favorites(user_id=1, query='query1', sentence_id=2, link='/results?query=query2'),
            Favorites(user_id=1, query='query2', sentence_id=5, link='/results?query=query2'),
        ]
        self.user_service.user_repo.get_user_favorites.return_value = user_favorites

        result = self.user_service.personalise_search_results(user_info, search_results)
        expected_results = [
            HTMLSentence(id=2, star='true'),
            HTMLSentence(id=5, star='true'),
            HTMLSentence(id=1),
            HTMLSentence(id=3),
            HTMLSentence(id=4),
        ]

        # Check that the results are as expected
        self.assertEqual(result, expected_results)

        # Check that the star attribute is correctly set
        for sentence in result:
            if sentence.id in {2, 5}:
                self.assertEqual(sentence.star, 'true')
            else:
                self.assertEqual(sentence.star, 'false')

    def test_get_user_favorites(self):
        user_info = UserInfo(
            user_id=1, username='user1', email='sample@gmail.com',
            password_hash='fnd28fhn3', salt='salt'.encode()
        )
        user_favorites = [
            Favorites(user_id=1, query='query1', sentence_id=2, link='/results?query=query1'),
            Favorites(user_id=1, query='query2', sentence_id=3, link='/results?query=query2'),
            Favorites(user_id=1, query='query2', sentence_id=5, link='/results?query=query2'),
        ]
        sentences = {
            2: Sentence(sentence_id=2, position_in_text=2, sentence_text='sent2', lemmatized_sentence=''),
            3: Sentence(sentence_id=3, position_in_text=3, sentence_text='sent3', lemmatized_sentence=''),
            5: Sentence(sentence_id=5, position_in_text=1, sentence_text='sent5', lemmatized_sentence=''),
        }
        self.user_service.user_repo.get_user_favorites.return_value = user_favorites
        self.user_service.transcript_repo.get_sentence_by_id.side_effect = sentences.get
        favorites = self.user_service.get_user_favorites(user_info)

        expected_favorites = [
            HTMLFavorites(query_text='query1', query_link='/results?query=query1', sentences=[(2, 'sent2')]),
            HTMLFavorites(query_text='query2', query_link='/results?query=query2', sentences=[
                (3, 'sent3'),
                (5, 'sent5')
            ]),
        ]
        self.assertEqual(len(favorites), len(expected_favorites))
        self.assertEqual(favorites, expected_favorites)
