# AI Recipe Persistence & Publishing — Implementation Plan (v2)

This document is the **authoritative end-to-end plan**: data model, APIs, file-by-file code changes, UI behaviour, security, testing, and rollout. Improvements from the v1 self-review are **folded into the main approach** (not optional add-ons).

---

## 1. Executive summary

| Decision | Choice |
|----------|--------|
| Storage | Single `Recipe` + `RecipeIngredient` rows |
| AI origin | New boolean `recipe.is_ai_generated` (default `False`) |
| Private vs public | Existing `recipe.is_public` — **no parallel table** |
| Publish later | `PATCH`/`POST` visibility endpoint flips `is_public`; **`is_ai_generated` never cleared** |
| Payload normalisation | **Server-side** function so OpenAI shape drift does not crash saves |
| My Meals | **Fix incorrect “Public” badge** in the same delivery as AI tabs |
| Defaults | Named constants for category/cooking time; optional **`max_cooking_time`** in save JSON from Pantry |

**Phases:** M1 schema + shared helpers → M2 save API + normaliser → M3 Pantry UI (full cards + save + success UX) → M4 My Meals tabs + visibility API + badge fixes → M5 detail + discover + partials + `api_recipes` → M6 tests + README.

---

## 2. Goals, non-goals, acceptance criteria

### Goals

- Pantry: AI cards show **full** ingredients + instructions (escaped HTML), visually aligned with `pt-card` matching section.
- **Save for me** → private AI recipe; **Save & publish** → public in one step.
- **Publish later** / **Make private** from My Meals and recipe detail (owner only).
- Badges: “AI generated” wherever a recipe card or title appears for `is_ai_generated` recipes.
- Success UX after private save: links for **View recipe**, **Edit before publishing**, **Publish now** (optional third calls same visibility API).

### Non-goals (v1)

- Moderation queue; clearing `is_ai_generated`; importing other users’ AI output.

### Acceptance checklist

- [ ] Private AI recipe: `is_public=False`, never in Discover / `api_recipes` / home / community / `public_profile` queries.
- [ ] Public AI recipe: appears in those queries with badge.
- [ ] My Meals shows correct **Private** vs **Public** for every owned recipe.
- [ ] `POST /api/ai/save-recipe` validates, normalises ingredients, returns `slug`.
- [ ] Visibility endpoint: 403 non-owner, 404 missing slug.
- [ ] Unit tests: save (private/public), normaliser, visibility toggle; optional Selenium happy path.

---

## 3. User journeys (integrated UX)

| # | Journey | UI | Persistence |
|---|---------|-----|----------------|
| A | Save private | Pantry → **Save to my AI recipes** | `is_ai_generated=True`, `is_public=False` |
| B | Save public | Pantry → **Save & publish** | `is_ai_generated=True`, `is_public=True` |
| C | Publish later | My Meals tab “From AI (private)” or recipe detail | `is_public=True` |
| D | Make private | Detail (owner) or My Meals | `is_public=False` (any owned recipe — **not** only AI; product may restrict to AI-only if desired) |
| E | Edit then publish | After A, user taps **Edit** then later **Publish** | Same as C |

**Post-save banner (Pantry, after successful save):**  
Inline HTML block: “Saved.” + `<a href="/recipe/{slug}">View</a>` · `<a href="/recipe/{slug}/edit">Edit</a>` · `<button data-publish>...</button>` if saved private — third action POSTs `{public:true}` to visibility URL.

---

## 4. Data model and migration

### 4.1 `app/models.py` — `Recipe` class

**Location:** after `is_deleted` (around line 67 in current file).

**Add column:**

```python
is_ai_generated = db.Column(db.Boolean, default=False, nullable=False)
```

**Optional index** (only if you filter heavily by this column):

```python
# In __table_args__ or separate:
# db.Index('ix_recipe_ai_public', 'is_ai_generated', 'is_public')  # optional v2
```

**Future-proof comment** (above the field):

```python
# If we add more origins (import URL, meal kit), consider recipe_source enum instead of booleans.
```

### 4.2 Alembic migration

**File:** `migrations/versions/<new>_add_recipe_is_ai_generated.py`  
**Down revision:** current head (e.g. `b8d71730109e` if nothing newer).

**SQLite-safe pattern:**

```python
def upgrade():
    with op.batch_alter_table('recipe', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('is_ai_generated', sa.Boolean(), nullable=False, server_default='0')
        )


def downgrade():
    with op.batch_alter_table('recipe', schema=None) as batch_op:
        batch_op.drop_column('is_ai_generated')
```

After deploy, you may run a follow-up migration to **drop `server_default`** so new inserts rely on app default only (optional cleanup).

### 4.3 Defaults for AI-created rows (constants)

**New module** `app/ai/recipe_defaults.py` (or top of `app/ai/services.py`):

```python
DEFAULT_AI_CATEGORY = 'dinner'
DEFAULT_AI_COOKING_TIME = 30
MAX_INSTRUCTIONS_LEN = 20000
MAX_INGREDIENT_ROWS = 40
MAX_INGREDIENT_NAME_LEN = 100
```

**Cooking time rule:** `cooking_time = min(payload.get('max_cooking_time') or DEFAULT_AI_COOKING_TIME, 480)` clamped, or from Pantry `maxTime` when building save payload.

**Category rule:** Map diet select to category when possible (`vegetarian` → `vegetarian`, `vegan` → `vegan`, else `DEFAULT_AI_CATEGORY`).

---

## 5. Server-side normalisation (required)

### 5.1 `app/ai/services.py` (or `app/ai/persistence.py`)

Add **`normalize_save_ingredients(raw_list) -> list[dict]`**:

- Accept `None` → `[]`.
- Iterate each item:
  - If `isinstance(item, str)`: strip → `{'name': item[:MAX], 'quantity': '', 'unit': ''}` if non-empty name.
  - If `dict`: read `name` / `title` / `ingredient` (first non-empty wins), `quantity`, `unit`; strip strings; truncate name.
- Drop entries with empty name after strip.
- If length > `MAX_INGREDIENT_ROWS`, slice or return validation error (prefer **400** with message).

Add **`validate_ai_save_payload(title, instructions, ingredients) -> tuple[str | None, list]`**  
Returns `(error_message, normalised_ingredients)` or `(None, ingredients)`.

- `title`: 1–200 chars, strip.
- `instructions`: non-empty after strip, max length.
- At least one normalised ingredient.

**Why here:** Both `save-recipe` and any future import can reuse the same logic.

---

## 6. API specification

### 6.1 `POST /api/ai/save-recipe`

| Item | Value |
|------|--------|
| Blueprint | `app/ai/routes.py` (keeps AI flows together) **or** `recipes` if you prefer all `Recipe` writes there |
| Decorators | `@bp.route(...)`, `@login_required` |
| CSRF | JSON + `X-CSRFToken` (same as `planner.js`) |

**Request JSON:**

```json
{
  "title": "string",
  "instructions": "string",
  "ingredients": ["egg", {"name": "spinach", "quantity": "2", "unit": "cups"}],
  "visibility": "private",
  "max_cooking_time": 30,
  "diet_hint": "vegetarian"
}
```

- `visibility`: only `"private"` or `"public"` (else 400).
- `max_cooking_time` / `diet_hint`: optional; drive `cooking_time` / `category` per §4.3.

**Handler pseudocode:**

```python
data = request.get_json(silent=True) or {}
err, ingredients = validate_ai_save_payload(...)
if err:
    return jsonify(success=False, error=err), 400
recipe = Recipe(
    title=...,
    description=...,  # optional excerpt from instructions[:200]
    instructions=instructions_stripped,
    cooking_time=...,
    category=...,
    creator_id=current_user.id,
    is_public=(data['visibility'] == 'public'),
    is_ai_generated=True,
)
db.session.add(recipe)
db.session.flush()
recipe.generate_slug()
for row in ingredients:
    db.session.add(RecipeIngredient(recipe_id=recipe.id, ...))
db.session.commit()
return jsonify(success=True, slug=recipe.slug, id=recipe.id)
```

**Rate limiting (recommended):** Reuse `last_ai_call` window **or** add `User.last_ai_save_at` — simpler v1: allow max **10 saves per hour** per user using a lightweight query on `Recipe` where `is_ai_generated` and `created_at > now-1h` and `creator_id==me`; if count ≥ 10 return **429** with message.

**Idempotency (v2):** Optional `client_id` UUID; store in memory/redis not required for coursework — document as future.

### 6.2 `POST /api/recipe/<slug>/visibility` (name aligned with existing `/recipe/...` URLs)

| Item | Value |
|------|--------|
| File | `app/recipes/routes.py` |
| Methods | `POST` |
| Auth | `@login_required` |

**Body:** `{"public": true}` or `{"public": false}`

**Logic:**

```python
recipe = Recipe.query.filter_by(slug=slug, is_deleted=False).first_or_404()
if recipe.creator_id != current_user.id:
    abort(403)
recipe.is_public = bool(public)
db.session.commit()
return jsonify(success=True, is_public=recipe.is_public)
```

**Validation:** If `public` is true, ensure `recipe.instructions` non-empty and at least one ingredient (same as publish quality gate); else 400.

**Note:** Use `slug` in path to match `detail`, `edit`, `delete` patterns in `recipes/routes.py`.

### 6.3 CSRF registration

`app/__init__.py` — no exempt needed if using header token on JSON POSTs (current app pattern).

---

## 7. Backend file-by-file code changes

### 7.1 `app/models.py`

- Add `is_ai_generated` column on `Recipe` as in §4.1.

### 7.2 `migrations/versions/<new>_add_recipe_is_ai_generated.py`

- As §4.2.

### 7.3 `app/ai/services.py`

- Add `normalize_save_ingredients`, `validate_ai_save_payload`, and optionally `map_diet_to_category(diet_hint: str) -> str`.
- Keep `get_ai_suggestions` unchanged unless you tighten the prompt to always return `{name, quantity?, unit?}` for each ingredient (recommended one-line prompt addition).

### 7.4 `app/ai/routes.py`

- Import `Recipe`, `RecipeIngredient` from `app.models`.
- New route `save_ai_recipe` calling validators + transaction.
- Do **not** duplicate normalisation in the route — call service functions only.

### 7.5 `app/recipes/routes.py`

**`my_meals` (currently lines 386–395):**

Replace single query with either:

**Option A — three queries (clearest for templates):**

```python
owned = Recipe.query.filter_by(creator_id=current_user.id, is_deleted=False)
manual_recipes = owned.filter_by(is_ai_generated=False).order_by(...).all()
ai_private = owned.filter(Recipe.is_ai_generated.is_(True), Recipe.is_public.is_(False)).order_by(...).all()
ai_public = owned.filter(Recipe.is_ai_generated.is_(True), Recipe.is_public.is_(True)).order_by(...).all()
```

**Option B — one query + Jinja split:** pass `recipes=all` and use `{% if recipe.is_ai_generated and not recipe.is_public %}` — fewer queries but messier template.

Recommend **Option A** and pass explicit variables to `my_meals.html`.

**New route:** `recipe_visibility` as §6.2.

**`api_recipes` (lines 109–127):** extend each dict:

```python
'is_ai_generated': bool(r.is_ai_generated),
```

**`home`, `discover`:** no query change (`is_public` already required). Templates receive ORM objects — badge in Jinja.

**`detail` route:** no change unless you add `can_publish` flag:

```python
can_publish = current_user.is_authenticated and recipe.creator_id == current_user.id and not recipe.is_public
```

Pass to template for button visibility.

### 7.6 `app/auth/routes.py`

- **`public_profile` (lines 113–117):** already `is_public=True` — **no code change**; AI public recipes appear automatically once `is_ai_generated` is set.

### 7.7 `app/community/routes.py`

- Leaderboard joins `Recipe` with `is_public` / `is_deleted` filters — verify filters remain **unchanged** so AI-generated public recipes count like any other public recipe (no `is_ai_generated == False` exclusion).

### 7.8 `app/planner/routes.py`

- **`planner()` recipe dropdown (line 49–51 area):** today:

```python
Recipe.query.filter(
    (Recipe.creator_id == current_user.id) | (Recipe.is_public == True)
).filter_by(is_deleted=False)
```

Private AI recipes **should** appear for the owner in the planner — already satisfied by `creator_id`. No change unless a bug excludes private; confirm `is_public` branch does not hide own private recipes (it should not — OR condition). **Verify manually.**

---

## 8. Frontend file-by-file code changes

### 8.1 `app/static/js/pantry.js`

**Add** (copy from `discover.js` lines 164–168 pattern):

```javascript
function escapeHtml(str) {
    if (str == null) return '';
    const div = document.createElement('div');
    div.appendChild(document.createTextNode(String(str)));
    return div.innerHTML;
}
```

**Refactor `renderResults`:**

1. **Matching block** — leave structure; optionally add `escapeHtml` for titles if not already safe (titles from DB are less risky than AI).

2. **AI block** — for each `s`:
   - Build card with `pt-card` wrapper to match grid.
   - Title: `escapeHtml(s.title)`.
   - Instructions: `escapeHtml(s.instructions)` inside `<div class="instructions-text" style="white-space:pre-wrap">`.
   - Ingredients: map `s.ingredients` — if element is string, treat as name; else use `.name`.
   - Append two buttons with `data-action="save-ai"` `data-visibility="private|public"` `data-index="${idx}"` OR store suggestions in a module-level `window.__lastAiSuggestions = [...]` after render (simpler than huge data attributes).

3. **Event delegation** on `resultsContainer`:

```javascript
resultsContainer.addEventListener('click', function (e) {
    const btn = e.target.closest('[data-action="save-ai"]');
    if (!btn) return;
    btn.disabled = true;
    const idx = parseInt(btn.dataset.index, 10);
    const suggestion = lastSuggestions[idx];
    fetch('/api/ai/save-recipe', { method: 'POST', headers: {...}, body: JSON.stringify({
        title: suggestion.title,
        instructions: suggestion.instructions,
        ingredients: suggestion.ingredients,
        visibility: btn.dataset.visibility,
        max_cooking_time: parseInt(document.getElementById('maxTime').value, 10) || null,
        diet_hint: document.getElementById('dietSelect').value || null,
    })})
    .then(...)
    .finally(() => { btn.disabled = false; });
});
```

4. **Double-submit:** disable **both** save buttons on that card while `fetch` in flight (`card.querySelectorAll('button[data-action="save-ai"]')`).

### 8.2 `app/templates/ai/pantry.html`

- Optional: add a hidden `<div id="save-feedback"></div>` below results for post-save banner.

### 8.3 `app/templates/recipes/my_meals.html`

**Bug fix (lines 26–30):** replace unconditional `Public` badge with:

```jinja2
{% if recipe.is_deleted %}
<span class="badge bg-danger">Deleted</span>
{% elif recipe.is_public %}
<span class="badge bg-success">Public</span>
{% else %}
<span class="badge bg-secondary">Private</span>
{% endif %}
{% if recipe.is_ai_generated %}
<span class="badge badge-ai ms-1">AI</span>
{% endif %}
```

**Tabs:** Bootstrap `nav-tabs` + `tab-pane`:

| Tab id | Content |
|--------|---------|
| `all` | `manual_recipes` + optional merge rule (all non-deleted owned except split?) — simplest: **All** = every owned `Recipe` not deleted, sorted by date |
| `ai-private` | `ai_private` list only |
| `ai-published` | `ai_public` list only |

Per-card actions:

- Always: View, Edit, Delete (existing patterns).
- If `recipe.is_ai_generated and not recipe.is_public`: show **Publish** button (`data-slug`, `fetch` visibility).
- If `recipe.is_ai_generated and recipe.is_public`: show **Make private** (optional).

### 8.4 `app/templates/recipes/detail.html`

**After title (line ~16):**

```jinja2
{% if recipe.is_ai_generated %}
<span class="badge badge-ai align-middle ms-2">AI generated</span>
{% endif %}
```

**Owner toolbar (inside `{% if current_user.is_authenticated %}` block near save button):**

```jinja2
{% if recipe.creator_id == current_user.id and not recipe.is_deleted %}
  {% if not recipe.is_public %}
  <button type="button" id="btn-publish-recipe" class="btn btn-sm btn-mint">Publish</button>
  {% elif recipe.is_ai_generated %}
  <button type="button" id="btn-unpublish-recipe" class="btn btn-sm btn-outline-light">Make private</button>
  {% endif %}
{% endif %}
```

**New script block** (or `static/js/recipe-visibility.js` included only on detail):

- `fetch('/api/recipe/' + slug + '/visibility', { method: 'POST', body: JSON.stringify({public: true}), headers: { 'Content-Type': 'application/json', 'X-CSRFToken': ... } })`
- On success: `location.reload()` or update badges in-place.

### 8.5 `app/templates/partials/_recipe_card.html`

After category badge (line ~10):

```jinja2
{% if recipe.is_ai_generated %}
<span class="badge badge-ai ms-1">AI</span>
{% endif %}
```

### 8.6 `app/static/js/discover.js` — `buildRecipeCard`

Add to returned HTML when `r.is_ai_generated`:

```javascript
${r.is_ai_generated ? '<span class="badge badge-ai ms-1">AI</span>' : ''}
```

Ensure `escapeHtml` does not double-escape badge HTML (inject badge **outside** escaped title string).

### 8.7 `app/templates/recipes/home.html` & `community/feed.html`

- Any inline recipe cards: add same `{% if recipe.is_ai_generated %}` badge as partial where ORM object exists.
- If feed uses a different partial, grep for `pt-card` / recipe loops and add badge consistently.

### 8.8 `app/static/css/style.css`

```css
.badge-ai {
  background-color: var(--pt-violet);
  color: var(--pt-bg);
  font-size: 0.65rem;
  font-weight: 600;
  letter-spacing: 0.04em;
}
[data-theme="light"] .badge-ai {
  color: #fff;
}
```

---

## 9. Query audit checklist (grep-driven)

Run ripgrep for `Recipe.query` / `recipe` listings and confirm **public** paths:

| File / area | Must include |
|-------------|----------------|
| `recipes/routes.py` `home` | `is_public=True`, `is_deleted=False` ✓ (line 18) |
| `discover` | same ✓ (line 52) |
| `api_recipes` | same ✓ (line 79) |
| `community/routes.py` feed | public recipes for non-followed stream ✓ |
| `auth/routes.py` `public_profile` | `is_public=True` ✓ |
| `auth/routes.py` `profile` | Own recipes — private AI **allowed** ✓ |
| `my_meals` | All `creator_id` — private AI **allowed** ✓ |

**Never** add `is_ai_generated` to a public filter unless the product goal is to hide AI from Discover (not in scope).

---

## 10. Security and limits

| Concern | Implementation |
|---------|----------------|
| XSS | `escapeHtml` in `pantry.js`; Jinja `{{ }}` on server |
| CSRF | Header on all POSTs |
| Body size | `MAX_CONTENT_LENGTH` already in `config.py` — ensure AI payload under limit |
| Abuse | Hourly save cap per §6.1 |
| Path traversal | N/A — no files from AI |

---

## 11. Testing plan (concrete)

### 11.1 `tests/unit/test_ai_recipe_save.py` (new)

- `normalize_save_ingredients` with strings, dicts, mixed, empty, >40 rows.
- `validate_ai_save_payload` too long title, empty instructions, no ingredients → errors.
- **Integration-style** with app context: create user, `POST` save with `TestConfig` CSRF off, assert DB row `is_ai_generated` and `is_public` flags.

### 11.2 Extend `tests/unit/test_recipes.py` or new file

- Visibility POST: owner 200, non-owner 403, wrong slug 404.
- After publish, recipe appears in `Recipe.query.filter_by(is_public=True)`.

### 11.3 Selenium (optional)

- Stub OpenAI or skip AI button; pre-seed user + call save API via `requests` in fixture is heavy — simpler: **manual test script** in README for team.

---

## 12. Rollout order (strict)

1. Migration + model (app boots, existing behaviour unchanged).
2. `services.py` normalisers + unit tests.
3. `POST /api/ai/save-recipe` + tests.
4. `pantry.js` render + save UI + success banner.
5. `POST /api/recipe/<slug>/visibility` + detail buttons + JS.
6. `my_meals` route + template tabs + badge fix.
7. Partials + `discover.js` + home/community badges.
8. README + AUDIT line.

---

## 13. Final review (v2 of the plan)

| Topic | Assessment |
|-------|------------|
| Single-table design | Still the right trade-off for planner/grocery/ratings. |
| Visibility API | Dedicated endpoint avoids overloading WTForms edit route. |
| My Meals badge fix | **Mandatory** in same release as AI private tab — documented with exact Jinja. |
| Normaliser in `services.py` | Reduces duplicate logic between future import and save. |
| Unpublish scope | Plan allows any owned recipe — **narrow to `is_ai_generated` only** if course staff expect “only AI can be unpublished without delete”; document team choice in PR. |
| `api_recipes` | Easy to miss — explicitly listed in §7.5 and §8.6. |
| Planner dropdown | Explicit verification step — good catch for private recipes. |

**Optional v3 enhancements:** `client_id` idempotency; drop migration `server_default`; admin filter for AI spam; prompt versioning column `ai_prompt_version`.

---

*Document version: 2.0 — integrated improvements, code-level specifications, file references aligned to `project-CITS3403-1` layout.*
