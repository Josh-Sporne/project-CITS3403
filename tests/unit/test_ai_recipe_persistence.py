import unittest

from app import create_app, db
from app.models import Recipe, RecipeIngredient, User
from app.ai.services import normalize_save_ingredients, validate_ai_save_payload
from config import TestConfig


class AiRecipePersistenceTestCase(unittest.TestCase):

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

    def test_normalize_ingredients_strings_and_dicts(self):
        raw = ['egg', {'name': 'spinach', 'quantity': '1', 'unit': 'cup'}, {'title': 'salt'}]
        out = normalize_save_ingredients(raw)
        self.assertEqual(len(out), 3)
        self.assertEqual(out[0]['name'], 'egg')
        self.assertEqual(out[1]['name'], 'spinach')
        self.assertEqual(out[1]['quantity'], '1')
        self.assertEqual(out[2]['name'], 'salt')

    def test_validate_payload_rejects_empty(self):
        err, _ = validate_ai_save_payload('', 'instructions', [['x']])
        self.assertIsNotNone(err)
        err, _ = validate_ai_save_payload('Title', '', [['x']])
        self.assertIsNotNone(err)
        err, _ = validate_ai_save_payload('Title', 'ok', [])
        self.assertIsNotNone(err)

    def test_validate_payload_accepts_clean(self):
        err, payload = validate_ai_save_payload(
            'My Dish',
            'Step one.\nStep two.',
            ['a', {'name': 'b', 'quantity': '2'}],
        )
        self.assertIsNone(err)
        self.assertEqual(payload['title'], 'My Dish')
        self.assertEqual(len(payload['ingredients']), 2)

    def test_save_ai_recipe_requires_login(self):
        resp = self.client.post(
            '/api/ai/save-recipe',
            json={
                'title': 'T',
                'instructions': 'Do it.',
                'ingredients': ['x'],
                'visibility': 'private',
            },
        )
        self.assertEqual(resp.status_code, 302)

    def test_private_recipe_hidden_from_anonymous(self):
        u = User(username='u3', email='u3@example.com')
        u.set_password('pass12345')
        db.session.add(u)
        db.session.flush()
        r = Recipe(
            title='Secret',
            description='',
            instructions='Nope.',
            cooking_time=10,
            category='dinner',
            creator_id=u.id,
            is_public=False,
            is_ai_generated=False,
        )
        db.session.add(r)
        db.session.flush()
        r.generate_slug()
        db.session.commit()

        resp = self.client.get('/recipe/' + r.slug)
        self.assertEqual(resp.status_code, 404)

        self.client.post('/login', data={
            'username': 'u3',
            'password': 'pass12345',
            'submit': 'Sign In',
        })
        ok = self.client.get('/recipe/' + r.slug)
        self.assertEqual(ok.status_code, 200)

    def test_save_ai_recipe_creates_row(self):
        u = User(username='u1', email='u1@example.com')
        u.set_password('pass12345')
        db.session.add(u)
        db.session.commit()

        with self.client.session_transaction() as sess:
            sess['_user_id'] = str(u.id)
            sess['_fresh'] = True

        resp = self.client.post(
            '/api/ai/save-recipe',
            json={
                'title': 'AI Toast',
                'instructions': 'Toast bread.\nButter.',
                'ingredients': ['bread', 'butter'],
                'visibility': 'private',
                'max_cooking_time': 15,
                'diet_hint': 'vegan',
            },
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get('success'))
        self.assertIn('slug', data)

        recipe = Recipe.query.filter_by(slug=data['slug']).first()
        self.assertIsNotNone(recipe)
        self.assertTrue(recipe.is_ai_generated)
        self.assertFalse(recipe.is_public)
        self.assertEqual(recipe.creator_id, u.id)
        self.assertGreaterEqual(RecipeIngredient.query.filter_by(recipe_id=recipe.id).count(), 1)

    def test_visibility_toggle_owner(self):
        u = User(username='u2', email='u2@example.com')
        u.set_password('pass12345')
        db.session.add(u)
        db.session.flush()

        r = Recipe(
            title='Private AI',
            description='',
            instructions='Cook.',
            cooking_time=20,
            category='dinner',
            creator_id=u.id,
            is_public=False,
            is_ai_generated=True,
        )
        db.session.add(r)
        db.session.flush()
        r.generate_slug()
        db.session.add(RecipeIngredient(recipe_id=r.id, name='salt', quantity='', unit=''))
        db.session.commit()
        slug = r.slug

        with self.client.session_transaction() as sess:
            sess['_user_id'] = str(u.id)
            sess['_fresh'] = True

        resp = self.client.post(
            '/api/recipe/' + slug + '/visibility',
            json={'public': True},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.get_json()['is_public'])
        db.session.refresh(r)
        self.assertTrue(r.is_public)
