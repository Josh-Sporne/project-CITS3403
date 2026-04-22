import unittest
from datetime import date, timedelta

from app import create_app, db
from app.models import (
    MealPlan, MealPlanItem, PantryItem, Recipe, RecipeIngredient, User,
)
from config import TestConfig


class PlannerTestCase(unittest.TestCase):

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

    def _setup_planner_data(self):
        """Create a user with two recipes on a meal plan for the current week."""
        user = User(username='planner', email='planner@example.com')
        user.set_password('testpass123')
        db.session.add(user)
        db.session.commit()

        recipe_a = Recipe(
            title='Recipe A', instructions='Do A.',
            cooking_time=10, category='dinner', creator_id=user.id,
        )
        recipe_a.generate_slug()
        recipe_b = Recipe(
            title='Recipe B', instructions='Do B.',
            cooking_time=20, category='lunch', creator_id=user.id,
        )
        recipe_b.generate_slug()
        db.session.add_all([recipe_a, recipe_b])
        db.session.commit()

        db.session.add(RecipeIngredient(
            recipe_id=recipe_a.id, name='garlic', quantity='2', unit='cloves',
        ))
        db.session.add(RecipeIngredient(
            recipe_id=recipe_b.id, name='garlic', quantity='3', unit='cloves',
        ))
        db.session.add(RecipeIngredient(
            recipe_id=recipe_b.id, name='pasta', quantity='200', unit='g',
        ))
        db.session.commit()

        today = date.today()
        monday = today - timedelta(days=today.weekday())
        plan = MealPlan(user_id=user.id, week_start=monday)
        db.session.add(plan)
        db.session.commit()

        db.session.add(MealPlanItem(
            mealplan_id=plan.id, recipe_id=recipe_a.id,
            day_of_week=0, meal_type='dinner',
        ))
        db.session.add(MealPlanItem(
            mealplan_id=plan.id, recipe_id=recipe_b.id,
            day_of_week=1, meal_type='lunch',
        ))
        db.session.commit()

        return user, recipe_a, recipe_b, plan

    def test_grocery_aggregation(self):
        user, *_ = self._setup_planner_data()

        self.client.post('/login', data={
            'username': 'planner',
            'password': 'testpass123',
            'submit': 'Sign In',
        })

        resp = self.client.get('/api/grocery-list?range=week')
        self.assertEqual(resp.status_code, 200)

        data = resp.get_json()
        items = data['items']
        names = [item['name'] for item in items]

        self.assertIn('garlic', [n.lower() for n in names])
        self.assertIn('pasta', [n.lower() for n in names])
        self.assertEqual(len(names), len(set(n.lower() for n in names)),
                         'Ingredients should be aggregated (no duplicates)')

    def test_pantry_excludes_from_grocery(self):
        user, *_ = self._setup_planner_data()

        db.session.add(PantryItem(user_id=user.id, ingredient_name='garlic'))
        db.session.commit()

        self.client.post('/login', data={
            'username': 'planner',
            'password': 'testpass123',
            'submit': 'Sign In',
        })

        resp = self.client.get('/api/grocery-list?range=week')
        self.assertEqual(resp.status_code, 200)

        data = resp.get_json()
        items = data['items']

        garlic_item = next(
            (i for i in items if i['name'].lower() == 'garlic'), None
        )
        self.assertIsNotNone(garlic_item, 'garlic should still appear in list')
        self.assertTrue(garlic_item['in_pantry'],
                        'garlic should be marked as in_pantry=true')
        self.assertGreater(data['excluded_count'], 0)


if __name__ == '__main__':
    unittest.main()
