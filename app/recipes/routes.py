import os
import uuid

from flask import (
    current_app, flash, jsonify, redirect, render_template, request, url_for,
)
from flask_login import current_user, login_required
from sqlalchemy import func

from app import db
from app.models import Comment, Rating, Recipe, RecipeIngredient, SavedRecipe
from app.recipes import bp
from app.recipes.forms import CATEGORY_CHOICES, RecipeForm


@bp.route('/')
def home():
    base = Recipe.query.filter_by(is_public=True, is_deleted=False)

    trending_recipes = (
        base
        .outerjoin(Rating, Rating.recipe_id == Recipe.id)
        .outerjoin(SavedRecipe, SavedRecipe.recipe_id == Recipe.id)
        .group_by(Recipe.id)
        .order_by(
            (func.count(func.distinct(Rating.id)) + func.count(func.distinct(SavedRecipe.id))).desc(),
            Recipe.created_at.desc(),
        )
        .limit(6)
        .all()
    )

    new_recipes = (
        base
        .order_by(Recipe.created_at.desc())
        .limit(3)
        .all()
    )

    return render_template(
        'recipes/home.html',
        trending_recipes=trending_recipes,
        new_recipes=new_recipes,
    )


@bp.route('/discover')
def discover():
    page = request.args.get('page', 1, type=int)
    per_page = 12

    query = Recipe.query.filter_by(is_public=True, is_deleted=False)
    total = query.count()

    recipes = (
        query
        .order_by(Recipe.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return render_template(
        'recipes/discover.html',
        recipes=recipes,
        categories=CATEGORY_CHOICES,
        total=total,
    )


@bp.route('/api/recipes')
def api_recipes():
    q = request.args.get('q', '', type=str).strip()
    category = request.args.get('category', '', type=str).strip()
    sort = request.args.get('sort', 'newest', type=str)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 12, type=int)

    query = Recipe.query.filter_by(is_public=True, is_deleted=False)

    if q:
        query = query.filter(Recipe.title.ilike(f'%{q}%'))
    if category:
        query = query.filter_by(category=category)

    if sort == 'rating':
        avg_sub = (
            db.session.query(
                Rating.recipe_id,
                func.avg(Rating.score).label('avg_score'),
            )
            .group_by(Rating.recipe_id)
            .subquery()
        )
        query = (
            query
            .outerjoin(avg_sub, Recipe.id == avg_sub.c.recipe_id)
            .order_by(func.coalesce(avg_sub.c.avg_score, 0).desc(), Recipe.created_at.desc())
        )
    elif sort == 'fastest':
        query = query.order_by(Recipe.cooking_time.asc(), Recipe.created_at.desc())
    else:
        query = query.order_by(Recipe.created_at.desc())

    total = query.count()
    recipes = query.offset((page - 1) * per_page).limit(per_page).all()
    has_next = (page * per_page) < total

    data = []
    for r in recipes:
        data.append({
            'id': r.id,
            'title': r.title,
            'slug': r.slug,
            'description': r.description or '',
            'cooking_time': r.cooking_time,
            'category': r.category,
            'image_filename': r.image_filename,
            'avg_rating': r.avg_rating,
            'rating_count': r.rating_count,
            'save_count': r.save_count,
            'creator': {
                'username': r.creator.username,
                'avatar_url': r.creator.avatar_url,
            },
            'created_at': r.created_at.isoformat() if r.created_at else None,
        })

    return jsonify(recipes=data, total=total, has_next=has_next)


@bp.route('/recipe/create', methods=['GET', 'POST'])
@login_required
def create():
    form = RecipeForm()

    if form.validate_on_submit():
        recipe = Recipe(
            title=form.title.data,
            description=form.description.data or '',
            cooking_time=form.cooking_time.data or 30,
            category=form.category.data,
            instructions=form.instructions.data,
            creator_id=current_user.id,
        )
        recipe.generate_slug()

        if form.image.data:
            image = form.image.data
            ext = image.filename.rsplit('.', 1)[-1].lower()
            filename = f'{uuid.uuid4().hex}.{ext}'
            upload_dir = current_app.config['UPLOAD_FOLDER']
            os.makedirs(upload_dir, exist_ok=True)
            image.save(os.path.join(upload_dir, filename))
            recipe.image_filename = filename

        db.session.add(recipe)
        db.session.flush()

        names = request.form.getlist('ingredient_name[]')
        qtys = request.form.getlist('ingredient_qty[]')
        units = request.form.getlist('ingredient_unit[]')
        for name, qty, unit in zip(names, qtys, units):
            name = name.strip()
            if not name:
                continue
            ingredient = RecipeIngredient(
                recipe_id=recipe.id,
                name=name,
                quantity=qty.strip(),
                unit=unit.strip(),
            )
            db.session.add(ingredient)

        db.session.commit()
        flash('Recipe created successfully!', 'success')
        return redirect(url_for('recipes.detail', slug=recipe.slug))

    return render_template('recipes/create.html', form=form, edit=False)


@bp.route('/recipe/<slug>')
def detail(slug):
    recipe = Recipe.query.filter_by(slug=slug, is_deleted=False).first_or_404()

    avg_rating = recipe.avg_rating
    rating_count = recipe.rating_count
    comments = recipe.comments.all()
    ingredients = recipe.ingredients.all()

    user_saved = False
    user_rating = 0
    if current_user.is_authenticated:
        user_saved = SavedRecipe.query.filter_by(
            user_id=current_user.id, recipe_id=recipe.id,
        ).first() is not None
        existing_rating = Rating.query.filter_by(
            user_id=current_user.id, recipe_id=recipe.id,
        ).first()
        if existing_rating:
            user_rating = existing_rating.score

    return render_template(
        'recipes/detail.html',
        recipe=recipe,
        avg_rating=avg_rating,
        rating_count=rating_count,
        comments=comments,
        ingredients=ingredients,
        user_saved=user_saved,
        user_rating=user_rating,
    )


@bp.route('/recipe/<slug>/edit', methods=['GET', 'POST'])
@login_required
def edit(slug):
    recipe = Recipe.query.filter_by(slug=slug, is_deleted=False).first_or_404()
    if recipe.creator_id != current_user.id:
        from flask import abort
        abort(403)

    form = RecipeForm(obj=recipe)

    if request.method == 'GET':
        ingredients = recipe.ingredients.all()
        return render_template(
            'recipes/create.html',
            form=form,
            edit=True,
            recipe=recipe,
            ingredients=ingredients,
        )

    if form.validate_on_submit():
        recipe.title = form.title.data
        recipe.description = form.description.data or ''
        recipe.cooking_time = form.cooking_time.data or 30
        recipe.category = form.category.data
        recipe.instructions = form.instructions.data

        if form.image.data:
            if recipe.image_filename:
                old_path = os.path.join(
                    current_app.config['UPLOAD_FOLDER'], recipe.image_filename,
                )
                if os.path.exists(old_path):
                    os.remove(old_path)

            image = form.image.data
            ext = image.filename.rsplit('.', 1)[-1].lower()
            filename = f'{uuid.uuid4().hex}.{ext}'
            upload_dir = current_app.config['UPLOAD_FOLDER']
            os.makedirs(upload_dir, exist_ok=True)
            image.save(os.path.join(upload_dir, filename))
            recipe.image_filename = filename

        RecipeIngredient.query.filter_by(recipe_id=recipe.id).delete()

        names = request.form.getlist('ingredient_name[]')
        qtys = request.form.getlist('ingredient_qty[]')
        units = request.form.getlist('ingredient_unit[]')
        for name, qty, unit in zip(names, qtys, units):
            name = name.strip()
            if not name:
                continue
            ingredient = RecipeIngredient(
                recipe_id=recipe.id,
                name=name,
                quantity=qty.strip(),
                unit=unit.strip(),
            )
            db.session.add(ingredient)

        db.session.commit()
        flash('Recipe updated successfully!', 'success')
        return redirect(url_for('recipes.detail', slug=recipe.slug))

    ingredients = recipe.ingredients.all()
    return render_template(
        'recipes/create.html',
        form=form,
        edit=True,
        recipe=recipe,
        ingredients=ingredients,
    )


@bp.route('/recipe/<slug>/delete', methods=['POST'])
@login_required
def delete(slug):
    recipe = Recipe.query.filter_by(slug=slug).first_or_404()
    if recipe.creator_id != current_user.id:
        from flask import abort
        abort(403)

    recipe.is_deleted = True
    db.session.commit()
    flash('Recipe deleted.', 'success')
    return redirect(url_for('recipes.my_meals'))


@bp.route('/recipe/<slug>/rate', methods=['POST'])
@login_required
def rate(slug):
    recipe = Recipe.query.filter_by(slug=slug, is_deleted=False).first_or_404()
    data = request.get_json(silent=True) or {}
    score = data.get('score', 0)

    if not isinstance(score, int) or score < 1 or score > 5:
        return jsonify(success=False, error='Score must be 1-5'), 400

    existing = Rating.query.filter_by(
        user_id=current_user.id, recipe_id=recipe.id,
    ).first()

    if existing:
        existing.score = score
    else:
        rating = Rating(
            user_id=current_user.id,
            recipe_id=recipe.id,
            score=score,
        )
        db.session.add(rating)

    db.session.commit()

    return jsonify(
        success=True,
        avg_rating=recipe.avg_rating,
        rating_count=recipe.rating_count,
    )


@bp.route('/recipe/<slug>/comment', methods=['POST'])
@login_required
def comment(slug):
    recipe = Recipe.query.filter_by(slug=slug, is_deleted=False).first_or_404()
    data = request.get_json(silent=True) or {}
    body = (data.get('body') or '').strip()

    if not body:
        return jsonify(success=False, error='Comment cannot be empty'), 400

    c = Comment(
        user_id=current_user.id,
        recipe_id=recipe.id,
        body=body,
    )
    db.session.add(c)
    db.session.commit()

    return jsonify(
        success=True,
        comment={
            'id': c.id,
            'author': current_user.username,
            'body': c.body,
            'created_at': c.created_at.isoformat() if c.created_at else None,
        },
    )


@bp.route('/recipe/<slug>/save', methods=['POST'])
@login_required
def save(slug):
    recipe = Recipe.query.filter_by(slug=slug, is_deleted=False).first_or_404()

    existing = SavedRecipe.query.filter_by(
        user_id=current_user.id, recipe_id=recipe.id,
    ).first()

    if existing:
        db.session.delete(existing)
        saved = False
    else:
        sr = SavedRecipe(user_id=current_user.id, recipe_id=recipe.id)
        db.session.add(sr)
        saved = True

    db.session.commit()
    return jsonify(success=True, saved=saved)


@bp.route('/my-meals')
@login_required
def my_meals():
    recipes = (
        Recipe.query
        .filter_by(creator_id=current_user.id)
        .order_by(Recipe.created_at.desc())
        .all()
    )
    return render_template('recipes/my_meals.html', recipes=recipes)
