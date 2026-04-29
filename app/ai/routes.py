from datetime import datetime, timezone, timedelta

from flask import render_template, request, jsonify, current_app
from flask_login import login_required, current_user

from app import db
from app.models import PantryItem, Recipe, RecipeIngredient
from app.ai import bp
from app.ai.recipe_defaults import (
    DEFAULT_AI_COOKING_TIME,
    MAX_AI_SAVES_PER_HOUR,
)
from app.ai.services import (
    get_pantry_matches,
    get_ai_suggestions,
    map_diet_to_category,
    validate_ai_save_payload,
)


@bp.route('/pantry')
@login_required
def pantry():
    items = PantryItem.query.filter_by(user_id=current_user.id).all()
    return render_template('ai/pantry.html', pantry_items=items)


@bp.route('/api/ai/suggest', methods=['POST'])
@login_required
def ai_suggest():
    now = datetime.now(timezone.utc)
    if current_user.last_ai_call:
        elapsed = now - current_user.last_ai_call.replace(tzinfo=timezone.utc)
        if elapsed < timedelta(seconds=30):
            wait = 30 - int(elapsed.total_seconds())
            return jsonify(
                success=False,
                error=f'Rate limited — please wait {wait}s'
            ), 429

    data = request.get_json(silent=True) or {}
    ingredients = data.get('ingredients', [])
    preferences = data.get('preferences', '')
    use_ai = data.get('use_ai', False)

    if not ingredients:
        return jsonify(success=False, error='No ingredients provided'), 400

    PantryItem.query.filter_by(user_id=current_user.id).delete()
    for name in ingredients:
        name = name.strip()
        if name:
            db.session.add(PantryItem(
                user_id=current_user.id,
                ingredient_name=name,
            ))
    db.session.commit()

    matches = get_pantry_matches(current_user.id)

    ai_suggestions = []
    if use_ai:
        api_key = current_app.config.get('OPENAI_API_KEY')
        ai_suggestions = get_ai_suggestions(ingredients, preferences, api_key)

    current_user.last_ai_call = now
    db.session.commit()

    return jsonify(
        success=True,
        matches=matches,
        ai_suggestions=ai_suggestions,
    )


@bp.route('/api/ai/save-recipe', methods=['POST'])
@login_required
def save_ai_recipe():
    data = request.get_json(silent=True) or {}
    err, payload = validate_ai_save_payload(
        data.get('title'),
        data.get('instructions'),
        data.get('ingredients'),
    )
    if err:
        return jsonify(success=False, error=err), 400

    vis = (data.get('visibility') or '').lower()
    if vis not in ('private', 'public'):
        return jsonify(
            success=False, error='visibility must be "private" or "public"',
        ), 400

    since = datetime.now(timezone.utc) - timedelta(hours=1)
    recent_saves = Recipe.query.filter(
        Recipe.creator_id == current_user.id,
        Recipe.is_ai_generated.is_(True),
        Recipe.created_at >= since,
    ).count()
    if recent_saves >= MAX_AI_SAVES_PER_HOUR:
        return jsonify(
            success=False,
            error=f'You can save at most {MAX_AI_SAVES_PER_HOUR} AI recipes per hour.',
        ), 429

    max_t = data.get('max_cooking_time')
    try:
        ct = int(max_t) if max_t is not None and str(max_t).strip() != '' else DEFAULT_AI_COOKING_TIME
    except (TypeError, ValueError):
        ct = DEFAULT_AI_COOKING_TIME
    ct = max(1, min(ct, 480))

    category = map_diet_to_category(data.get('diet_hint'))
    instr = payload['instructions']
    description = ''
    if instr:
        first_line = instr.split('\n', 1)[0].strip()
        description = first_line[:200] if first_line else ''

    recipe = Recipe(
        title=payload['title'],
        description=description,
        instructions=instr,
        cooking_time=ct,
        category=category,
        creator_id=current_user.id,
        is_public=(vis == 'public'),
        is_ai_generated=True,
    )
    db.session.add(recipe)
    db.session.flush()
    recipe.generate_slug()

    for row in payload['ingredients']:
        db.session.add(RecipeIngredient(
            recipe_id=recipe.id,
            name=row['name'],
            quantity=row['quantity'],
            unit=row['unit'],
        ))

    db.session.commit()
    return jsonify(success=True, slug=recipe.slug, id=recipe.id)
