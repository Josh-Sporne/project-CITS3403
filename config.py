import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config:
    # SECRET_KEY MUST come from the environment. No hardcoded fallback so that
    # missing config fails loudly at startup rather than silently using a
    # well-known dev key in production. Validated in app/__init__.py create_app.
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'instance', 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(basedir, 'app', 'static', 'uploads')
    MAX_CONTENT_LENGTH = 4 * 1024 * 1024
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    PEXELS_API_KEY = os.environ.get('PEXELS_API_KEY')


class TestConfig(Config):
    TESTING = True
    # Tests don't need a real secret — explicit value so the production
    # validation in create_app doesn't trip when running pytest.
    SECRET_KEY = 'test-secret-key-not-for-production'
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
    WTF_CSRF_ENABLED = False
    SERVER_NAME = 'localhost.localdomain'
