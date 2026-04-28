import json

from app import db
from app.models import Recipe, RecipeIngredient, PantryItem


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
