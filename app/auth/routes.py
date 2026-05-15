import uuid
import os

from flask import flash, redirect, render_template, request, url_for, current_app, jsonify
from flask_login import current_user, login_required, login_user, logout_user

from sqlalchemy import func

from app import db
from app.auth import bp
from app.auth.forms import EditProfileForm, LoginForm, RegisterForm
from app.models import Follower, Rating, Recipe, SavedRecipe, User, Comment


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

    comments = Comment.query.filter_by(user_id=current_user.id).order_by(Comment.created_at.desc()).all()
    comment_list=[]
    for i in range(len(comments)):
        comment_list.append(Recipe.query.filter_by(id=comments[i].recipe_id).all() + [comments[i]])

    ratings = Rating.query.filter_by(user_id=current_user.id).order_by(Rating.created_at.desc()).all()
    rating_list=[]
    for i in range(len(ratings)):
        rating_list.append(Recipe.query.filter_by(id=ratings[i].recipe_id).all() + [ratings[i]])

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
        if edit_form.new_username.data != "":
            current_user.username=edit_form.new_username.data
        if edit_form.new_email.data != "":
            current_user.email=edit_form.new_email.data
        if edit_form.new_password.data != "":
            current_user.set_password(edit_form.new_password.data)
        if edit_form.image.data:
            image = edit_form.image.data
            ext = image.filename.rsplit('.', 1)[-1].lower()
            filename = f'{uuid.uuid4().hex}.{ext}'
            upload_dir = current_app.config['UPLOAD_FOLDER']
            os.makedirs(upload_dir, exist_ok=True)
            image.save(os.path.join(upload_dir, filename))
            current_user.avatar = url_for('static', filename='uploads/' + filename)
        db.session.commit()
        flash('Profile updated!', 'success')
    else:
        for field, errors in edit_form.errors.items():
            field=field.replace("_", " ").capitalize()
            for error in errors:
                error=error.replace("_", " ").lower()
                flash(f'{field} {error}', 'danger')
    return redirect(url_for('auth.profile')+"#settings-pane")

@bp.route('/api/followers/<username>')
@login_required
def api_followers(username):
    user = User.query.filter_by(username=username).first_or_404()
    follows = Follower.query.filter_by(followed_id=user.id).all()
    followers=[]
    for item in follows:
        followers+=User.query.filter_by(id=item.follower_id).all()
    return jsonify([{
        'username': u.username,
        'avatar_url': u.avatar_url,
        'is_following': current_user.is_following(u)
    } for u in followers])

@bp.route('/api/following/<username>')
@login_required
def api_following(username):
    user = User.query.filter_by(username=username).first_or_404()
    follows = Follower.query.filter_by(follower_id=user.id).all()
    following=[]
    for item in follows:
        following+=User.query.filter_by(id=item.followed_id).all()
    return jsonify([{
        'username': u.username,
        'avatar_url': u.avatar_url,
        'is_following': current_user.is_following(u)
    } for u in following])

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

    comments = Comment.query.filter_by(user_id=user.id).order_by(Comment.created_at.desc()).all()
    comment_list=[]
    for i in range(len(comments)):
        comment_list.append(Recipe.query.filter_by(id=comments[i].recipe_id).all() + [comments[i]])
    
    ratings = Rating.query.filter_by(user_id=current_user.id).order_by(Rating.created_at.desc()).all()
    rating_list=[]
    for i in range(len(ratings)):
        rating_list.append(Recipe.query.filter_by(id=ratings[i].recipe_id).all() + [ratings[i]])

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
    q = ''
    users = User.query.filter(User.username.ilike(f'%{q}%')).limit(20).all()
    total = len(users)
    has_next = 12<total
    return render_template('auth/users.html', users=users, total=total, has_next=has_next)


@bp.route('/api/users')
def api_users():
    q = request.args.get('q', '', type=str).strip()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 12, type=int)

    query = User.query

    if q:
        query = query.filter(User.username.ilike(f'%{q}%'))

    total = query.count()
    users = query.offset((page - 1) * per_page).limit(per_page).all()
    has_next = (page * per_page) < total

    return jsonify(users=users, total=total, has_next=has_next)
