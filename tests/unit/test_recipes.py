import unittest

from app import create_app, db
from app.models import Recipe, RecipeIngredient, User
from config import TestConfig


class RecipeTestCase(unittest.TestCase):

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

    def _register_and_login(self, username='chef', email='chef@example.com',
                            password='testpass123'):
        self.client.post('/register', data={
            'username': username,
            'email': email,
            'password': password,
            'confirm_password': password,
            'submit': 'Create Account',
        })

    def test_create_recipe(self):
        self._register_and_login()

        resp = self.client.post('/recipe/create', data={
            'title': 'Garlic Pasta',
            'instructions': 'Boil pasta. Add garlic.',
            'cooking_time': '20',
            'category': 'dinner',
            'ingredient_name[]': ['garlic', 'pasta'],
            'ingredient_qty[]': ['2', '200'],
            'ingredient_unit[]': ['cloves', 'g'],
            'submit': 'Submit',
        }, follow_redirects=False)

        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Recipe.query.count(), 1)

        recipe = Recipe.query.first()
        self.assertEqual(recipe.slug, 'garlic-pasta')
        self.assertEqual(RecipeIngredient.query.count(), 2)

        ingredients = RecipeIngredient.query.filter_by(recipe_id=recipe.id).all()
        names = sorted([i.name for i in ingredients])
        self.assertEqual(names, ['garlic', 'pasta'])

    def test_edit_recipe_by_non_owner(self):
        user_a = User(username='user_a', email='a@example.com')
        user_a.set_password('pass1234')
        user_b = User(username='user_b', email='b@example.com')
        user_b.set_password('pass1234')
        db.session.add_all([user_a, user_b])
        db.session.commit()

        recipe = Recipe(
            title='Secret Recipe',
            instructions='Top secret.',
            cooking_time=10,
            category='dinner',
            creator_id=user_b.id,
        )
        recipe.generate_slug()
        db.session.add(recipe)
        db.session.commit()

        self.client.post('/login', data={
            'username': 'user_a',
            'password': 'pass1234',
            'submit': 'Sign In',
        })

        resp = self.client.get(f'/recipe/{recipe.slug}/edit')
        self.assertEqual(resp.status_code, 403)


if __name__ == '__main__':
    unittest.main()
