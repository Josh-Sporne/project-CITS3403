import unittest

from app import create_app, db
from app.models import User
from config import TestConfig


class AuthTestCase(unittest.TestCase):

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

    def test_register_creates_user(self):
        resp = self.client.post('/register', data={
            'username': 'alice',
            'email': 'alice@example.com',
            'password': 'securepass123',
            'confirm_password': 'securepass123',
            'submit': 'Create Account',
        }, follow_redirects=False)

        self.assertEqual(resp.status_code, 302)
        self.assertEqual(User.query.count(), 1)

        user = User.query.first()
        self.assertEqual(user.username, 'alice')
        self.assertEqual(user.email, 'alice@example.com')
        self.assertNotEqual(user.password_hash, 'securepass123')
        self.assertTrue(user.check_password('securepass123'))

    def test_login_success(self):
        u = User(username='bob', email='bob@example.com')
        u.set_password('mypassword')
        db.session.add(u)
        db.session.commit()

        resp = self.client.post('/login', data={
            'username': 'bob',
            'password': 'mypassword',
            'submit': 'Sign In',
        }, follow_redirects=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'bob', resp.data)

    def test_login_wrong_password(self):
        u = User(username='carol', email='carol@example.com')
        u.set_password('correctpass')
        db.session.add(u)
        db.session.commit()

        resp = self.client.post('/login', data={
            'username': 'carol',
            'password': 'wrongpass',
            'submit': 'Sign In',
        }, follow_redirects=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Invalid', resp.data)

    def test_protected_route_redirects(self):
        resp = self.client.get('/planner', follow_redirects=False)

        self.assertEqual(resp.status_code, 302)
        self.assertIn('/login', resp.headers['Location'])


if __name__ == '__main__':
    unittest.main()
