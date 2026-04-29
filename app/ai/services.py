import json

from app import db
from app.models import Recipe, RecipeIngredient, PantryItem
from app.ai.recipe_defaults import (
    DEFAULT_AI_CATEGORY,
    DEFAULT_AI_COOKING_TIME,
    MAX_INSTRUCTIONS_LEN,
    MAX_INGREDIENT_ROWS,
    MAX_INGREDIENT_NAME_LEN,
)
from app.recipes.forms import CATEGORY_CHOICES

_VALID_CATEGORIES = {c[0] for c in CATEGORY_CHOICES}


def get_pantry_matches(user_id):
    pantry_names = {
        p.ingredient_name.lower()
        for p in PantryItem.query.filter_by(user_id=user_id).all()
    }
    if not pantry_names:
        return []

    recipes = Recipe.query.filter_by(
        is_public=True, is_deleted=False
    ).all()

    results = []
    for recipe in recipes:
        ingredients = RecipeIngredient.query.filter_by(
            recipe_id=recipe.id
        ).all()
        total = len(ingredients)
        if total == 0:
            continue
        matched = sum(
            1 for ing in ingredients
            if ing.name.lower().strip() in pantry_names
        )
        match_pct = round((matched / total) * 100, 1)
        results.append({
            'recipe_id': recipe.id,
            'title': recipe.title,
            'slug': recipe.slug,
            'cooking_time': recipe.cooking_time,
            'category': recipe.category,
            'match_pct': match_pct,
            'total_ingredients': total,
            'matched_ingredients': matched,
        })

    results.sort(key=lambda x: x['match_pct'], reverse=True)
    return results[:10]


def normalize_save_ingredients(raw_list):
    """Coerce OpenAI / client ingredient shapes into dicts for RecipeIngredient."""
    if not raw_list:
        return []
    out = []
    for item in raw_list[:MAX_INGREDIENT_ROWS]:
        if isinstance(item, str):
            name = item.strip()
            if name:
                out.append({
                    'name': name[:MAX_INGREDIENT_NAME_LEN],
                    'quantity': '',
                    'unit': '',
                })
        elif isinstance(item, dict):
            name = (
                item.get('name')
                or item.get('title')
                or item.get('ingredient')
                or ''
            )
            name = str(name).strip()
            if not name:
                continue
            qty = str(item.get('quantity') or '').strip()[:50]
            unit = str(item.get('unit') or '').strip()[:30]
            out.append({
                'name': name[:MAX_INGREDIENT_NAME_LEN],
                'quantity': qty,
                'unit': unit,
            })
    return out


def map_diet_to_category(diet_hint):
    """Map Pantry diet select value to a valid Recipe.category slug."""
    if not diet_hint:
        return DEFAULT_AI_CATEGORY
    d = str(diet_hint).lower().strip()
    if d in _VALID_CATEGORIES:
        return d
    return DEFAULT_AI_CATEGORY


def validate_ai_save_payload(title, instructions, ingredients_raw):
    """
    Returns (error_message, None) or (None, payload dict).
    payload: title, instructions, ingredients (list of dicts with name, quantity, unit).
    """
    title = (title or '').strip()
    if not title or len(title) > 200:
        return 'Title must be 1–200 characters.', None

    instructions = (instructions or '').strip()
    if not instructions:
        return 'Instructions are required.', None
    if len(instructions) > MAX_INSTRUCTIONS_LEN:
        return 'Instructions are too long.', None

    ingredients = normalize_save_ingredients(ingredients_raw)
    if not ingredients:
        return 'At least one ingredient is required.', None

    return None, {
        'title': title,
        'instructions': instructions,
        'ingredients': ingredients,
    }


def get_ai_suggestions(ingredients, preferences, api_key):
    if not api_key or api_key == 'sk-placeholder':
        return []

    try:
        import openai

        client = openai.OpenAI(api_key=api_key)
        prompt = (
            "You are a creative chef. Given these ingredients: "
            f"{', '.join(ingredients)}. "
            f"User preferences: {preferences or 'none'}. "
            "Suggest exactly 5 meal ideas. Return ONLY valid JSON — "
            "an array of objects with keys: title (string), "
            "ingredients (array of strings), instructions (string). "
            "No markdown, no explanation, just the JSON array."
        )

        response = client.chat.completions.create(
            model='gpt-3.5-turbo',
            messages=[{'role': 'user', 'content': prompt}],
            temperature=0.7,
            max_tokens=1200,
        )

        text = response.choices[0].message.content.strip()
        if text.startswith('```'):
            text = text.split('\n', 1)[1]
            text = text.rsplit('```', 1)[0]
        suggestions = json.loads(text)
        return suggestions if isinstance(suggestions, list) else []

    except Exception:
        return []
