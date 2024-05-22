import unittest
from datetime import datetime

from mathematicon.backend.model import UserInfo, SearchHistory, Favorites
from mathematicon.backend.repositories.user_repo import UserRepository


class TestUserRepository(unittest.TestCase):
    def setUp(self):
        self.db_path = ":memory:"
        self.user_repo = UserRepository(self.db_path)
        self.user_repo.create_tables()

        self.user_info = UserInfo(
            username='test_user', email='test_user@example.com',
            password_hash='hashed_password', salt=b'salt'
        )

    def tearDown(self):
        self.user_repo.close()

    def test_add_user(self):
        added_user = self.user_repo.add_user(self.user_info)
        self.assertIsNotNone(added_user.user_id)
        self.assertEqual(added_user.username, 'test_user')

    def test_update_history(self):
        self.user_repo.add_user(self.user_info)

        history = SearchHistory(user_id=1, query='test_query', timestamp=datetime.now().isoformat(), link='/result?query=test_query')
        self.user_repo.update_history(history, history_limit=2)

        # Add more history to exceed the limit
        for i in range(3):
            history = SearchHistory(user_id=1, query=f'test_query_{i}', timestamp=datetime.now().isoformat(), link=f'/result?query=test_query_{i}')
            self.user_repo.update_history(history, history_limit=2)

        cursor = self.user_repo.conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM user_history WHERE user_id = 1')
        count = cursor.fetchone()[0]
        self.assertEqual(count, 2)

    def test_add_favorites(self):
        added_user = self.user_repo.add_user(self.user_info)

        favorite = Favorites(user_id=added_user.user_id,
                             query='favorite_query',
                             sentence_id=1,
                             link='/result?query=favorite_query')
        self.user_repo.add_favorites(favorite)

        favorites = self.user_repo.get_user_favorites(added_user)
        self.assertEqual(len(favorites), 1)
        self.assertEqual(favorites[0].query, 'favorite_query')

    def test_remove_favorites(self):
        added_user = self.user_repo.add_user(self.user_info)
        favorite = Favorites(user_id=added_user.user_id,
                             query='favorite_query',
                             sentence_id=1,
                             link='/result?query=favorite_query')

        self.user_repo.add_favorites(favorite)
        self.user_repo.remove_favorites(favorite)

        favorites = self.user_repo.get_user_favorites(added_user)
        self.assertEqual(len(favorites), 0)

    def test_get_user_favorites(self):
        added_user = self.user_repo.add_user(self.user_info)

        favorites = [
            Favorites(user_id=added_user.user_id, query='favorite_query_1', sentence_id=1, link='/result?query=favorite_query_1'),
            Favorites(user_id=added_user.user_id, query='favorite_query_2', sentence_id=1, link='/result?query=favorite_query_2'),
        ]

        for fav in favorites:
            self.user_repo.add_favorites(fav)

        user_favorites = self.user_repo.get_user_favorites(added_user)
        self.assertEqual(len(user_favorites), 2)
        self.assertEqual(user_favorites[0].query, 'favorite_query_1')
        self.assertEqual(user_favorites[1].query, 'favorite_query_2')


if __name__ == '__main__':
    unittest.main()
