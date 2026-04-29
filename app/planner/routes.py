from datetime import date, timedelta, datetime, timezone

from flask import render_template, request, jsonify
from flask_login import login_required, current_user

from app import db
from app.models import (
    MealPlan, MealPlanItem, Recipe, RecipeIngredient, PantryItem,
)
from app.planner import bp


DAY_NAMES = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday',
             'Saturday', 'Sunday']
MEAL_TYPES = ['breakfast', 'lunch', 'dinner']


def _monday_of_week(d=None):
    d = d or date.today()
    return d - timedelta(days=d.weekday())


def _get_or_create_plan(user_id, week_start=None):
    week_start = week_start or _monday_of_week()
    plan = MealPlan.query.filter_by(
        user_id=user_id, week_start=week_start
    ).first()
    if plan is None:
        plan = MealPlan(user_id=user_id, week_start=week_start)
        db.session.add(plan)
        db.session.commit()
    return plan


@bp.route('/planner')
@login_required
def planner():
    plan = _get_or_create_plan(current_user.id)
    items = MealPlanItem.query.filter_by(mealplan_id=plan.id).all()

    grid = {}
    for day in range(7):
        grid[day] = {}
        for mt in MEAL_TYPES:
            grid[day][mt] = None
    for item in items:
        grid[item.day_of_week][item.meal_type] = item

    recipes = Recipe.query.filter(
        (Recipe.creator_id == current_user.id) | (Recipe.is_public == True)  # noqa: E712
    ).filter_by(is_deleted=False).order_by(Recipe.title).all()

    pantry = PantryItem.query.filter_by(user_id=current_user.id).all()

    return render_template(
        'planner/planner.html',
        plan=plan,
        grid=grid,
        day_names=DAY_NAMES,
        meal_types=MEAL_TYPES,
        recipes=recipes,
        pantry=pantry,
    )


@bp.route('/api/planner/save', methods=['POST'])
@login_required
def planner_save():
    data = request.get_json(silent=True) or {}
    day = data.get('day')
    meal_type = data.get('meal_type')
    recipe_id = data.get('recipe_id')
    custom_text = data.get('custom_text', '')

    if day is None or meal_type not in MEAL_TYPES:
        return jsonify(success=False, error='Invalid day or meal_type'), 400
    day = int(day)
    if day < 0 or day > 6:
        return jsonify(success=False, error='Day must be 0-6'), 400

    plan = _get_or_create_plan(current_user.id)
    item = MealPlanItem.query.filter_by(
        mealplan_id=plan.id, day_of_week=day, meal_type=meal_type
    ).first()

    if item is None:
        item = MealPlanItem(mealplan_id=plan.id, day_of_week=day,
                            meal_type=meal_type)
        db.session.add(item)

    if recipe_id:
        item.recipe_id = int(recipe_id)
        item.custom_text = ''
    else:
        item.recipe_id = None
        item.custom_text = custom_text

    db.session.commit()

    title = ''
    if item.recipe_id and item.recipe:
        title = item.recipe.title
    else:
        title = item.custom_text

    return jsonify(success=True, item={
        'id': item.id,
        'day': item.day_of_week,
        'meal_type': item.meal_type,
        'title': title,
    })


@bp.route('/api/planner/remove', methods=['POST'])
@login_required
def planner_remove():
    data = request.get_json(silent=True) or {}
    item_id = data.get('item_id')
    if not item_id:
        return jsonify(success=False, error='Missing item_id'), 400

    item = MealPlanItem.query.get(int(item_id))
    if item is None:
        return jsonify(success=False, error='Not found'), 404

    if item.meal_plan.user_id != current_user.id:
        return jsonify(success=False, error='Forbidden'), 403

    db.session.delete(item)
    db.session.commit()
    return jsonify(success=True)


@bp.route('/grocery')
@login_required
def grocery():
    return render_template('planner/grocery.html')


@bp.route('/api/grocery-list')
@login_required
def grocery_list():
    range_type = request.args.get('range', 'week')
    days_param = request.args.get('days', '')

    plan = _get_or_create_plan(current_user.id)
    query = MealPlanItem.query.filter_by(mealplan_id=plan.id)

    if range_type == 'day':
        today_idx = date.today().weekday()
        query = query.filter_by(day_of_week=today_idx)
    elif range_type == 'custom' and days_param:
        day_nums = [int(d.strip()) for d in days_param.split(',') if d.strip().isdigit()]
        query = query.filter(MealPlanItem.day_of_week.in_(day_nums))

    items = query.all()

    pantry_names = {
        p.ingredient_name.lower()
        for p in PantryItem.query.filter_by(user_id=current_user.id).all()
    }

    ingredient_map = {}
    for item in items:
        if not item.recipe_id:
            continue
        for ri in RecipeIngredient.query.filter_by(recipe_id=item.recipe_id).all():
            key = ri.name.lower().strip()
            if key not in ingredient_map:
                ingredient_map[key] = {
                    'name': ri.name.strip(),
                    'quantities': [],
                    'unit': ri.unit or '',
                }
            if ri.quantity:
                ingredient_map[key]['quantities'].append(ri.quantity)

    grocery_items = []
    excluded_count = 0
    for key, info in sorted(ingredient_map.items()):
        in_pantry = key in pantry_names
        if in_pantry:
            excluded_count += 1
        grocery_items.append({
            'name': info['name'],
            'quantity': ', '.join(info['quantities']) if info['quantities'] else '',
            'unit': info['unit'],
            'in_pantry': in_pantry,
        })

    return jsonify(
        items=grocery_items,
        excluded_count=excluded_count,
        total_count=len(grocery_items),
    )
