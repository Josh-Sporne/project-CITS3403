from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, BooleanField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, Optional

from app.models import User


class RegisterForm(FlaskForm):
    username = StringField(
        'Username',
        validators=[DataRequired(), Length(min=3, max=80)],
    )
    email = StringField(
        'Email',
        validators=[DataRequired(), Email()],
    )
    password = PasswordField(
        'Password',
        validators=[DataRequired(), Length(min=8)],
    )
    confirm_password = PasswordField(
        'Confirm Password',
        validators=[DataRequired(), EqualTo('password', message='Passwords must match.')],
    )
    submit = SubmitField('Create Account')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already taken.')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class EditProfileForm(FlaskForm):
    bio = TextAreaField('Bio', validators=[Length(max=500)])
    new_username = StringField('New Username', validators=[Optional(), Length(3, 80)])
    new_email = StringField('New Email', validators=[Optional(), Email()])
    new_password = PasswordField('New Password', validators=[Optional(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password', validators=[EqualTo('new_password')])
    image = FileField('Profile Picture', validators=[Optional(), FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'])])
    submit = SubmitField('Save Changes')
    def validate_new_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('already taken.')

    def validate_new_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('already registered.')
        
