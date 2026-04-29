from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, IntegerField, SelectField
from wtforms.validators import DataRequired, Length, NumberRange, Optional

CATEGORY_CHOICES = [
    ('breakfast', 'Breakfast'),
    ('lunch', 'Lunch'),
    ('dinner', 'Dinner'),
    ('snack', 'Snack'),
    ('dessert', 'Dessert'),
    ('vegan', 'Vegan'),
    ('vegetarian', 'Vegetarian'),
    ('high-protein', 'High Protein'),
    ('quick-meals', 'Quick Meals'),
    ('one-pot', 'One Pot'),
]


class RecipeForm(FlaskForm):
    title = StringField(
        'Title',
        validators=[DataRequired(), Length(max=200)],
    )
    description = TextAreaField('Description', validators=[Optional()])
    cooking_time = IntegerField(
        'Cooking Time (minutes)',
        validators=[Optional(), NumberRange(min=1, max=480)],
    )
    category = SelectField('Category', choices=CATEGORY_CHOICES, default='dinner')
    instructions = TextAreaField('Instructions', validators=[DataRequired()])
    image = FileField(
        'Recipe Image',
        validators=[FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'])],
    )
