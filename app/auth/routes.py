
from flask import flash, redirect, render_template, request, url_for, current_app, jsonify
from flask_login import current_user, login_required, login_user, logout_user

from sqlalchemy import func

from app import db
from app.auth import bp
from app.auth.forms import EditProfileForm, LoginForm, RegisterForm
from app.models import Follower, Rating, Recipe, SavedRecipe, User, Comment
from app.utils import save_uploaded_image


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('auth.profile'))
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data.strip().lower()
        email = form.email.data.strip().lower()
        user = User(username=username, email=email)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash('Account created!', 'success')
        return redirect(url_for('recipes.home'))
    return render_template('auth/register.html', form=form)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('auth.profile'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter(func.lower(User.username) == form.username.data.lower()).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password.', 'danger')
            return redirect(url_for('auth.login'))
        login_user(user, remember=form.remember_me.data)
        flash('Welcome back!', 'success')
        from urllib.parse import urlparse
        nxt = request.args.get('next')
        if nxt:
            parsed = urlparse(nxt)
            if parsed.netloc or parsed.scheme:
                nxt = None
        return redirect(nxt or url_for('recipes.home'))
    return render_template('auth/login.html', form=form)


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out.', 'info')
    return redirect(url_for('recipes.home'))


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

    comment_list = (
        db.session.query(Recipe, Comment)
        .join(Comment, Comment.recipe_id == Recipe.id)
        .filter(Comment.user_id == current_user.id)
        .order_by(Comment.created_at.desc())
        .all()
    )

    rating_list = (
        db.session.query(Recipe, Rating)
        .join(Rating, Rating.recipe_id == Recipe.id)
        .filter(Rating.user_id == current_user.id)
        .order_by(Rating.created_at.desc())
        .all()
    )

    edit_form = EditProfileForm(obj=current_user)

    return render_template(
        'auth/profile.html',
        user=current_user,
        recipes=recipes,
        saved_recipes=saved,
        avg_rating=avg_rating,
        follower_count=follower_count,
        following_count=following_count,
        comment_list=comment_list,
        rating_list=rating_list,
        edit_form=edit_form,
    )

@bp.route('/profile', methods=['POST'])
@login_required
def profile_edit():
    edit_form = EditProfileForm(obj=current_user)
    if edit_form.validate_on_submit():
        current_user.bio = edit_form.bio.data
        # Fields are pre-filled with current values, so only commit a change
        # if the value actually differs — avoids needless DB writes.
        new_uname = (edit_form.new_username.data or '').strip().lower()
        if new_uname and new_uname != (current_user.username or '').lower():
            current_user.username = new_uname
        new_email = (edit_form.new_email.data or '').strip().lower()
        if new_email and new_email != (current_user.email or '').lower():
            current_user.email = new_email
        if edit_form.new_password.data != "":
            current_user.set_password(edit_form.new_password.data)
        if edit_form.image.data:
            filename = save_uploaded_image(edit_form.image.data)
            if filename:
                current_user.avatar = url_for('static', filename='uploads/' + filename)
        db.session.commit()
        flash('Profile updated!', 'success')
        # On success, drop the #settings-pane hash so the page opens on the
        # default "My Recipes" tab — closes the settings form and shows the
        # updated username in the page header at a glance.
        return redirect(url_for('auth.profile'))
    else:
        for field, errors in edit_form.errors.items():
            field=field.replace("_", " ").capitalize()
            for error in errors:
                error=error.replace("_", " ").lower()
                flash(f'{field} {error}', 'danger')
    # On error, stay on the settings tab so the user can fix and retry.
    return redirect(url_for('auth.profile')+"#settings-pane")

def _user_list_payload(user_ids):
    """Build the JSON payload used by /api/followers and /api/following.

    Batches the User fetch and the current_user is-following check into one
    query each, instead of issuing N queries inside a Python loop.
    """
    if not user_ids:
        return []
    users = User.query.filter(User.id.in_(user_ids)).all()
    current_following_ids = {
        f.followed_id
        for f in Follower.query.filter(
            Follower.follower_id == current_user.id,
            Follower.followed_id.in_(user_ids),
        ).all()
    }
    return [{
        'username': u.username,
        'avatar_url': u.avatar_url,
        'is_following': u.id in current_following_ids,
    } for u in users]


@bp.route('/api/followers/<username>')
@login_required
def api_followers(username):
    user = User.query.filter_by(username=username).first_or_404()
    follower_ids = [
        f.follower_id
        for f in Follower.query.filter_by(followed_id=user.id).all()
    ]
    return jsonify(_user_list_payload(follower_ids))


@bp.route('/api/following/<username>')
@login_required
def api_following(username):
    user = User.query.filter_by(username=username).first_or_404()
    followed_ids = [
        f.followed_id
        for f in Follower.query.filter_by(follower_id=user.id).all()
    ]
    return jsonify(_user_list_payload(followed_ids))

@bp.route('/user/<username>')
def public_profile(username):
    user = User.query.filter(func.lower(User.username) == username.lower()).first_or_404()

    recipes = (
        Recipe.query
        .filter_by(creator_id=user.id, is_public=True, is_deleted=False)
        .order_by(Recipe.created_at.desc())
        .all()
    )
    avg_rating = 0.0
    if recipes:
        result = (
            db.session.query(db.func.avg(Rating.score))
            .join(Recipe, Rating.recipe_id == Recipe.id)
            .filter(Recipe.creator_id == user.id, Recipe.is_deleted == False)
            .scalar()
        )
        avg_rating = round(result, 1) if result else 0.0

    comment_list = (
        db.session.query(Recipe, Comment)
        .join(Comment, Comment.recipe_id == Recipe.id)
        .filter(Comment.user_id == user.id)
        .order_by(Comment.created_at.desc())
        .all()
    )

    rating_list = (
        db.session.query(Recipe, Rating)
        .join(Rating, Rating.recipe_id == Recipe.id)
        .filter(Rating.user_id == user.id)
        .order_by(Rating.created_at.desc())
        .all()
    )

    follower_count = Follower.query.filter_by(followed_id=user.id).count()
    following_count = Follower.query.filter_by(follower_id=user.id).count()

    is_following = False
    if current_user.is_authenticated and current_user.id != user.id:
        is_following = current_user.is_following(user)

    return render_template(
        'auth/public_profile.html',
        user=user,
        recipes=recipes,
        avg_rating=avg_rating,
        follower_count=follower_count,
        is_following=is_following,
        following_count=following_count,
        comment_list=comment_list,
        rating_list=rating_list,
    )

@bp.route('/users')
def users():
    q = request.args.get('q', '', type=str).strip()
    query = User.query
    if q:
        query = query.filter(User.username.ilike(f'%{q}%'))
    users = query.order_by(User.username).limit(20).all()
    total = query.count()
    has_next = total > 20
    return render_template('auth/users.html', users=users, total=total, has_next=has_next, q=q)


@bp.route('/api/users')
def api_users():
    q = request.args.get('q', '', type=str).strip()
    page = max(request.args.get('page', 1, type=int), 1)
    per_page = max(1, min(request.args.get('per_page', 12, type=int), 50))

    query = User.query
    if q:
        query = query.filter(User.username.ilike(f'%{q}%'))

    total = query.count()
    users = query.offset((page - 1) * per_page).limit(per_page).all()
    has_next = (page * per_page) < total

    # SQLAlchemy User objects aren't JSON-serialisable directly — convert to dicts.
    return jsonify(
        users=[{
            'id': u.id,
            'username': u.username,
            'avatar_url': u.avatar_url,
        } for u in users],
        total=total,
        has_next=has_next,
    )
