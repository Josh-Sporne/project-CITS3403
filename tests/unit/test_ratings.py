import unittest

from app import create_app, db
from app.models import Rating, Recipe, User
from config import TestConfig


class RatingTestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def _make_user_and_recipe(self):
        user = User(username='tester', email='tester@example.com')
        user.set_password('testpass123')
        db.session.add(user)
        db.session.commit()

        recipe = Recipe(
            title='Ratable Dish',
            instructions='Make it.',
            cooking_time=15,
            category='dinner',
            creator_id=user.id,
        )
        recipe.generate_slug()
        db.session.add(recipe)
        db.session.commit()
        return user, recipe

    def test_rate_recipe_average(self):
        user, recipe = self._make_user_and_recipe()

        rater_a = User(username='rater_a', email='a@rate.com')
        rater_a.set_password('pass1234')
        rater_b = User(username='rater_b', email='b@rate.com')
        rater_b.set_password('pass1234')
        rater_c = User(username='rater_c', email='c@rate.com')
        rater_c.set_password('pass1234')
        db.session.add_all([rater_a, rater_b, rater_c])
        db.session.commit()

        db.session.add(Rating(user_id=rater_a.id, recipe_id=recipe.id, score=3))
        db.session.add(Rating(user_id=rater_b.id, recipe_id=recipe.id, score=4))
        db.session.add(Rating(user_id=rater_c.id, recipe_id=recipe.id, score=5))
        db.session.commit()

        self.assertEqual(recipe.avg_rating, 4.0)

    def test_duplicate_rating_updates(self):
        user, recipe = self._make_user_and_recipe()

        self.client.post('/login', data={
            'username': 'tester',
            'password': 'testpass123',
            'submit': 'Sign In',
        })

        self.client.post(
            f'/recipe/{recipe.slug}/rate',
            json={'score': 3},
        )
        self.assertEqual(Rating.query.count(), 1)
        self.assertEqual(Rating.query.first().score, 3)

        self.client.post(
            f'/recipe/{recipe.slug}/rate',
            json={'score': 5},
        )
        self.assertEqual(Rating.query.count(), 1)
        self.assertEqual(Rating.query.first().score, 5)


if __name__ == '__main__':
    unittest.main()
