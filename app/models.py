import hashlib
from datetime import datetime, timezone

from flask_login import UserMixin
from slugify import slugify
from werkzeug.security import generate_password_hash, check_password_hash

from app import db


class User(UserMixin, db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    bio = db.Column(db.Text, default='')
    last_ai_call = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    recipes = db.relationship('Recipe', backref='creator', lazy='dynamic')
    meal_plans = db.relationship('MealPlan', backref='owner', lazy='dynamic')
    ratings = db.relationship('Rating', backref='author', lazy='dynamic')
    comments = db.relationship('Comment', backref='author', lazy='dynamic')
    saved_recipes = db.relationship('SavedRecipe', backref='user', lazy='dynamic')
    pantry_items = db.relationship('PantryItem', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def avatar_url(self):
        digest = hashlib.md5(self.email.lower().encode()).hexdigest()
        return f'https://www.gravatar.com/avatar/{digest}?d=identicon&s=80'

    def is_following(self, user):
        return Follower.query.filter_by(
            follower_id=self.id, followed_id=user.id
        ).first() is not None

    def __repr__(self):
        return f'<User {self.username}>'


class Recipe(db.Model):
    __tablename__ = 'recipe'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, index=True)
    description = db.Column(db.Text, default='')
    instructions = db.Column(db.Text, nullable=False)
    cooking_time = db.Column(db.Integer, default=30)
    category = db.Column(db.String(50), index=True, default='dinner')
    image_filename = db.Column(db.String(256), nullable=True)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)
    is_public = db.Column(db.Boolean, default=True)
    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    ingredients = db.relationship(
        'RecipeIngredient', backref='recipe', lazy='dynamic',
        cascade='all, delete-orphan',
    )
    ratings = db.relationship('Rating', backref='recipe', lazy='dynamic')
    comments = db.relationship(
        'Comment', backref='recipe', lazy='dynamic',
        order_by='Comment.created_at.desc()',
    )
    saved_by = db.relationship('SavedRecipe', backref='recipe', lazy='dynamic')

    def generate_slug(self):
        base = slugify(self.title)
        slug = base
        counter = 1
        while Recipe.query.filter_by(slug=slug).first() is not None:
            slug = f'{base}-{counter}'
            counter += 1
        self.slug = slug

    @property
    def avg_rating(self):
        result = db.session.query(db.func.avg(Rating.score)).filter(
            Rating.recipe_id == self.id
        ).scalar()
        return round(result, 1) if result else 0.0

    @property
    def rating_count(self):
        return self.ratings.count()

    @property
    def save_count(self):
        return self.saved_by.count()

    def __repr__(self):
        return f'<Recipe {self.title}>'


class RecipeIngredient(db.Model):
    __tablename__ = 'recipe_ingredient'

    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'), index=True)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.String(50), default='')
    unit = db.Column(db.String(30), default='')


class MealPlan(db.Model):
    __tablename__ = 'meal_plan'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)
    week_start = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    items = db.relationship(
        'MealPlanItem', backref='meal_plan', lazy='dynamic',
        cascade='all, delete-orphan',
    )


class MealPlanItem(db.Model):
    __tablename__ = 'meal_plan_item'

    id = db.Column(db.Integer, primary_key=True)
    mealplan_id = db.Column(db.Integer, db.ForeignKey('meal_plan.id'))
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'), nullable=True)
    day_of_week = db.Column(db.Integer, nullable=False)  # 0=Mon .. 6=Sun
    meal_type = db.Column(db.String(20), default='dinner')  # breakfast/lunch/dinner
    custom_text = db.Column(db.String(200), default='')

    recipe = db.relationship('Recipe')


class Rating(db.Model):
    __tablename__ = 'rating'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'))
    score = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        db.UniqueConstraint('user_id', 'recipe_id', name='uq_user_recipe_rating'),
    )


class Comment(db.Model):
    __tablename__ = 'comment'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'))
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class SavedRecipe(db.Model):
    __tablename__ = 'saved_recipe'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'))
    saved_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        db.UniqueConstraint('user_id', 'recipe_id', name='uq_user_recipe_save'),
    )


class PantryItem(db.Model):
    __tablename__ = 'pantry_item'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)
    ingredient_name = db.Column(db.String(100), nullable=False)


class Follower(db.Model):
    __tablename__ = 'follower'

    id = db.Column(db.Integer, primary_key=True)
    follower_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    followed_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        db.UniqueConstraint('follower_id', 'followed_id', name='uq_follower_followed'),
    )
