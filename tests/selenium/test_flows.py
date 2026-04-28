import os
import threading
import time
import unittest

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options

from app import create_app, db
from app.models import Recipe, RecipeIngredient, User
from config import TestConfig


class SeleniumTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        TestConfig.SERVER_NAME = None
        cls.app = create_app(TestConfig)
        cls.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test_selenium.db'
        cls.app.config['WTF_CSRF_ENABLED'] = True
        cls.app.config['TESTING'] = False

        with cls.app.app_context():
            db.create_all()

            u = User(username='testuser', email='test@test.com')
            u.set_password('password123')
            db.session.add(u)

            u2 = User(username='otheruser', email='other@test.com')
            u2.set_password('password123')
            db.session.add(u2)
            db.session.flush()

            r = Recipe(
                title='Test Pasta',
                instructions='Cook it.',
                cooking_time=20,
                category='dinner',
                creator_id=u2.id,
            )
            r.generate_slug()
            db.session.add(r)
            db.session.flush()

            ri = RecipeIngredient(
                recipe_id=r.id, name='pasta', quantity='200', unit='g',
            )
            db.session.add(ri)
            db.session.commit()

        cls.server_thread = threading.Thread(
            target=cls.app.run,
            kwargs={'port': 5555, 'use_reloader': False},
        )
        cls.server_thread.daemon = True
        cls.server_thread.start()
        time.sleep(2)

        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        try:
            cls.driver = webdriver.Chrome(options=chrome_options)
        except Exception:
            cls.driver = None

    @classmethod
    def tearDownClass(cls):
        if cls.driver:
            cls.driver.quit()
        db_path = os.path.join(
            os.path.dirname(__file__), '..', '..', 'instance', 'test_selenium.db',
        )
        if os.path.exists(db_path):
            os.remove(db_path)

    def setUp(self):
        if not self.driver:
            self.skipTest('Chrome/chromedriver not available')
        self.base_url = 'http://localhost:5555'

    def _login(self, username='testuser', password='password123'):
        self.driver.get(f'{self.base_url}/login')
        wait = WebDriverWait(self.driver, 10)

        username_field = wait.until(
            EC.presence_of_element_located((By.NAME, 'username'))
        )
        username_field.clear()
        username_field.send_keys(username)

        password_field = self.driver.find_element(By.NAME, 'password')
        password_field.clear()
        password_field.send_keys(password)

        submit = self.driver.find_element(By.NAME, 'submit')
        submit.click()

        wait.until(lambda d: '/login' not in d.current_url)

    def test_register_flow(self):
        self.driver.get(f'{self.base_url}/register')
        wait = WebDriverWait(self.driver, 10)

        wait.until(EC.presence_of_element_located((By.NAME, 'username')))
        self.driver.find_element(By.NAME, 'username').send_keys('newuser')
        self.driver.find_element(By.NAME, 'email').send_keys('new@test.com')
        self.driver.find_element(By.NAME, 'password').send_keys('password123')
        self.driver.find_element(By.NAME, 'confirm_password').send_keys('password123')
        self.driver.find_element(By.NAME, 'submit').click()

        wait.until(lambda d: '/register' not in d.current_url)
        self.assertIn('newuser', self.driver.page_source)

    def test_login_flow(self):
        self._login('testuser', 'password123')
        self.assertIn('testuser', self.driver.page_source)

    def test_view_recipe(self):
        self._login()
        self.driver.get(f'{self.base_url}/recipe/test-pasta')

        wait = WebDriverWait(self.driver, 10)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, 'body')))

        page_text = self.driver.page_source
        self.assertTrue(
            'Test Pasta' in page_text,
            'Recipe title "Test Pasta" should appear on the detail page',
        )

    def test_discover_page(self):
        self.driver.get(f'{self.base_url}/discover')

        wait = WebDriverWait(self.driver, 10)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, 'body')))

        self.assertEqual(self.driver.execute_script(
            'return document.readyState'), 'complete')

        page_text = self.driver.page_source.lower()
        has_search = (
            'search' in page_text
            or len(self.driver.find_elements(By.CSS_SELECTOR, 'input[type="search"], input[type="text"]')) > 0
        )
        self.assertTrue(has_search, 'Discover page should have a search input')

    def test_create_recipe_flow(self):
        self._login()
        self.driver.get(f'{self.base_url}/recipe/create')

        wait = WebDriverWait(self.driver, 10)
        wait.until(EC.presence_of_element_located((By.NAME, 'title')))

        self.driver.find_element(By.NAME, 'title').send_keys('Selenium Recipe')
        self.driver.find_element(By.NAME, 'instructions').send_keys('Test instructions for selenium.')

        cooking_time_field = self.driver.find_element(By.NAME, 'cooking_time')
        cooking_time_field.clear()
        cooking_time_field.send_keys('15')

        self.driver.find_element(By.NAME, 'submit').click()

        wait.until(lambda d: '/recipe/create' not in d.current_url)
        self.assertIn('Selenium Recipe', self.driver.page_source)

    def test_community_page(self):
        self.driver.get(f'{self.base_url}/community')

        wait = WebDriverWait(self.driver, 10)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, 'body')))

        page_text = self.driver.page_source.lower()
        self.assertTrue(
            'community' in page_text,
            'Community page should contain "Community" heading',
        )


if __name__ == '__main__':
    unittest.main()
