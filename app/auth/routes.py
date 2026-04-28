from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app import db
from app.auth import bp
from app.auth.forms import EditProfileForm, LoginForm, RegisterForm
from app.models import Follower, Rating, Recipe, SavedRecipe, User


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('auth.profile'))

    form = RegisterForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash('Account created!', 'success')
        return redirect('/')
    return render_template('auth/register.html', form=form)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('auth.profile'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password.', 'danger')
            return redirect(url_for('auth.login'))
        login_user(user, remember=form.remember_me.data)
        flash('Welcome back!', 'success')
        next_page = request.args.get('next')
        return redirect(next_page or '/')
    return render_template('auth/login.html', form=form)


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out.', 'info')
    return redirect('/')


@bp.route('/profile')
@login_required
def profile():
    recipes = (
        Recipe.query
        .filter_by(creator_id=current_user.id, is_deleted=False)
        .order_by(Recipe.created_at.desc())
        .all()
    )

    saved = (
        db.session.query(Recipe)
        .join(SavedRecipe, SavedRecipe.recipe_id == Recipe.id)
        .filter(SavedRecipe.user_id == current_user.id, Recipe.is_deleted == False)
        .order_by(SavedRecipe.saved_at.desc())
        .all()
    )

    avg_rating = 0.0
    if recipes:
        result = (
            db.session.query(db.func.avg(Rating.score))
            .join(Recipe, Rating.recipe_id == Recipe.id)
            .filter(Recipe.creator_id == current_user.id, Recipe.is_deleted == False)
            .scalar()
        )
        avg_rating = round(result, 1) if result else 0.0

    follower_count = Follower.query.filter_by(followed_id=current_user.id).count()
    following_count = Follower.query.filter_by(follower_id=current_user.id).count()

    edit_form = EditProfileForm(obj=current_user)

    return render_template(
        'auth/profile.html',
        user=current_user,
        recipes=recipes,
        saved_recipes=saved,
        avg_rating=avg_rating,
        follower_count=follower_count,
        following_count=following_count,
        edit_form=edit_form,
    )


@bp.route('/profile/edit', methods=['POST'])
@login_required
def profile_edit():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.bio = form.bio.data
        db.session.commit()
        flash('Profile updated!', 'success')
    return redirect(url_for('auth.profile'))


@bp.route('/user/<username>')
def public_profile(username):
    user = User.query.filter_by(username=username).first_or_404()

    recipes = (
        Recipe.query
        .filter_by(creator_id=user.id, is_public=True, is_deleted=False)
        .order_by(Recipe.created_at.desc())
        .all()
    )

    follower_count = Follower.query.filter_by(followed_id=user.id).count()

    is_following = False
    if current_user.is_authenticated and current_user.id != user.id:
        is_following = current_user.is_following(user)

    return render_template(
        'auth/public_profile.html',
        user=user,
        recipes=recipes,
        follower_count=follower_count,
        is_following=is_following,
    )
