from datetime import datetime, timezone, timedelta

from flask import render_template, request, jsonify, current_app
from flask_login import login_required, current_user

from app import db
from app.models import PantryItem
from app.ai import bp
from app.ai.services import get_pantry_matches, get_ai_suggestions


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
