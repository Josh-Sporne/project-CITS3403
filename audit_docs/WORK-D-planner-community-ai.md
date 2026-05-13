# Person D — Planner, Community & AI
### Plate Theory · Workstream D

---

## Your role in one sentence
You own everything that happens **after a user finds a recipe** — planning meals, building a shopping list, seeing what the community is cooking, and getting AI suggestions from their pantry.

---

## Your primary files (you own these — others don't touch them)

| File | Why it's yours |
|---|---|
| `app/templates/planner/planner.html` | Meal planner grid |
| `app/templates/planner/grocery.html` | Grocery list page |
| `app/templates/community/feed.html` | Community feed |
| `app/templates/ai/pantry.html` | Pantry AI page |
| `app/static/js/planner.js` | All planner interactivity |
| `app/static/js/pantry.js` | Pantry AI interactivity |
| `app/planner/routes.py` | Planner backend routes |
| `app/community/routes.py` | Community backend routes |
| `app/ai/routes.py` | AI backend routes |
| `app/ai/services.py` | AI service logic |

---

## Shared files — how to coordinate

| File | Owner | What you need |
|---|---|---|
| `app/static/js/main.js` | **Person A** | Pull their branch before starting. You get `escapeHtml()`, `showErrorToast()`, and `toggleFollow()` for free. Replace all raw `innerHTML` in `planner.js` and `pantry.js` with `escapeHtml()`. Use `toggleFollow()` in `feed.html` instead of the inline follow logic. |
| `app/templates/recipes/detail.html` | **Person C** | The "Add to Meal Plan" button lives in Person C's file. You build the JS/backend side of the mini-modal; tell Person C what button HTML to add. |
| `app/templates/base.html` | **Person B** | If you need a base layout change (e.g. notification dot on nav), ask Person B. |

---

## Branch setup

```bash
# Pull Person A's branch first (requirements.txt + models.py), then:
git checkout main
git pull
git checkout -b feature/planner-community-ai
```

---

## 🔴 Critical — Planner meals are not clickable

### B3 + U1 + C-V13 · Clicking a meal name in the planner does nothing
**Files:** `app/templates/planner/planner.html`, `app/static/js/planner.js`

Recipe titles in planner slots are plain `<span>` text. This is the single most natural interaction users try and expect to work.

**Option A (simpler) — link to the recipe detail page:**
In `planner.html`, wherever the slot content is rendered, change:
```html
<span class="slot-content">{{ item.recipe.name }}</span>
```
to:
```html
<a class="slot-content text-decoration-none"
   href="{{ url_for('recipes.detail', slug=item.recipe.slug) }}">
  {{ item.recipe.name }}
</a>
```

**Option B (richer) — open a preview modal:**
Add a lightweight recipe-preview modal to `planner.html`:
```html
<div class="modal fade" id="recipePreviewModal" tabindex="-1">
  <div class="modal-dialog">
    <div class="modal-content pt-panel">
      <div class="modal-header">
        <h5 class="modal-title" id="previewTitle">Recipe</h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
      </div>
      <div class="modal-body" id="previewBody"><!-- populated by JS --></div>
      <div class="modal-footer">
        <a id="previewLink" href="#" class="btn btn-mint">View Full Recipe</a>
      </div>
    </div>
  </div>
</div>
```

In `planner.js`, add a click handler that fetches `/api/recipe-preview/<slug>` (or passes data from the existing slot data attribute) and populates the modal.

---

## 🔴 High — Day/Week toggle does nothing

### A3 + C17 + U6 + C-V2 · Day/Week toggle only changes grocery preview — the grid never changes
**Files:** `app/static/js/planner.js`, `app/templates/planner/planner.html`

Clicking "Day" only changes the grocery API call parameter. The 7-day grid always shows all 7 days.

**Fix in `planner.js`:**
```js
let currentRange = 'week'; // or 'day'

function setRange(range) {
  currentRange = range;
  document.querySelectorAll('.day-column').forEach(col => {
    const dayIndex = parseInt(col.dataset.dayIndex); // 0=Mon, 6=Sun
    const todayIndex = new Date().getDay() - 1; // adjust for Mon start
    if (range === 'day') {
      col.style.display = dayIndex === todayIndex ? '' : 'none';
    } else {
      col.style.display = '';
    }
  });
  // also update grocery preview as before
  updateGroceryPreview(range);
}
```

**Fix in `planner.html`:**
Add `data-day-index="0"` through `data-day-index="6"` to each day column div.

For C-V2 (Saturday/Sunday cut off on smaller screens), add to `style.css` (coordinate with Person C):
```css
.planner-grid {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}
.day-column {
  min-width: 120px;
}
```

---

## 🔴 High — "Add to Meal Plan" navigates away instead of opening a modal

### B2 + U7 + C-V9 · "Add to Meal Plan" on recipe detail goes to empty planner
**Files:** `app/static/js/planner.js`, `app/planner/routes.py`
*(Coordinate with Person C who owns `detail.html`)*

**Your backend part** — the existing `POST /api/planner/save` already works. No new route needed.

**Your JS part** — add a mini-modal that can be triggered from any page. Create a global function in `planner.js`:
```js
function openAddToPlanModal(recipeId, recipeName) {
  // populate the day + meal-type selectors
  // on save, call POST /api/planner/save with the selected day/meal_type/recipe_id
  // show success toast on completion
}
window.openAddToPlanModal = openAddToPlanModal;
```

**Tell Person C** to change the button in `detail.html` from:
```html
<a href="/planner" class="btn btn-mint">Add to Meal Plan</a>
```
to:
```html
<button class="btn btn-mint"
  onclick="openAddToPlanModal({{ recipe.id }}, {{ recipe.name|tojson }})">
  Add to Meal Plan
</button>
```

Also, add the actual mini-modal HTML to `planner.html` (or a `base.html` modal — coordinate with Person B). Minimum viable:
```html
<div class="modal fade" id="addToPlanModal" tabindex="-1">
  <div class="modal-dialog modal-sm">
    <div class="modal-content pt-panel">
      <div class="modal-header">
        <h6 class="modal-title">Add to Meal Plan</h6>
        <button class="btn-close" data-bs-dismiss="modal"></button>
      </div>
      <div class="modal-body">
        <p id="addToPlanRecipeName" class="fw-bold mb-3"></p>
        <select id="addToPlanDay" class="form-select mb-2">
          <option value="0">Monday</option>
          <option value="1">Tuesday</option>
          <option value="2">Wednesday</option>
          <option value="3">Thursday</option>
          <option value="4">Friday</option>
          <option value="5">Saturday</option>
          <option value="6">Sunday</option>
        </select>
        <select id="addToPlanMeal" class="form-select mb-3">
          <option value="breakfast">Breakfast</option>
          <option value="lunch">Lunch</option>
          <option value="dinner">Dinner</option>
          <option value="snack">Snack</option>
        </select>
        <button class="btn btn-mint w-100" onclick="saveAddToPlan()">Add</button>
      </div>
    </div>
  </div>
</div>
```

---

## 🔴 High — Grocery list quantity bug

### B6 + C-V5 · Grocery list shows "basil 1, 1 handful" instead of summing quantities
**File:** `app/planner/routes.py` (grocery-list aggregation)

When the same ingredient appears in multiple meals, quantities are joined as strings.
```python
# In the grocery list route, replace the string-join logic:
from collections import defaultdict

aggregated = defaultdict(list)
for item in meal_plan_items:
    for ingredient in item.recipe.ingredients:
        aggregated[ingredient.name].append(ingredient.quantity)

grocery_items = []
for name, quantities in aggregated.items():
    # Try to sum numeric quantities; fall back to listing
    total = None
    try:
        total = sum(float(q) for q in quantities if q)
        display = f'{total:g}' if total else ''
    except (ValueError, TypeError):
        display = ' + '.join(str(q) for q in quantities if q)
    grocery_items.append({'name': name, 'quantity': display})
```

Also fix the checkbox ID bug (D8) while you're in this file:

### D8 · Grocery checkbox IDs use raw ingredient names — spaces break the DOM
**File:** `app/templates/planner/grocery.html`
```html
<!-- Replace: -->
<input type="checkbox" id="gi-{{ item.name }}">
<!-- With: -->
<input type="checkbox" id="gi-{{ loop.index }}">
<label for="gi-{{ loop.index }}">{{ item.name }}</label>
```

---

## 🔴 High — Community feed

### G-UI-9 · Community feed fires N+1 DB queries (one per recipe card)
**File:** `app/community/routes.py`

`current_user.is_following(recipe.creator)` runs a DB query per recipe in the template. 30 recipes = 31 queries.
```python
# In the community route, pre-fetch followed IDs:
if current_user.is_authenticated:
    followed_ids = {f.followed_id for f in current_user.following}
else:
    followed_ids = set()
# Pass to template:
return render_template('community/feed.html', ..., followed_ids=followed_ids)
```
In the template:
```html
<!-- Replace: -->
{% if current_user.is_following(recipe.creator) %}
<!-- With: -->
{% if recipe.creator_id in followed_ids %}
```

### G-UI-2 · Community feed image height is inconsistent across cards
**File:** `app/templates/community/feed.html` (lines 53-58)

Recipes **with** an image render a bare `<img>` (no fixed height). Recipes **without** an image render `<div class="img-ph">` (fixed height). Cards are different heights.
```html
<!-- Replace the if/else image block with: -->
<div class="feed-card-img">
  {% if recipe.image_filename %}
    <img src="{{ url_for('static', filename='uploads/' + recipe.image_filename) }}"
         alt="{{ recipe.name }}">
  {% endif %}
</div>
```
Add to CSS (coordinate with Person C for `style.css`):
```css
.feed-card-img {
  height: 160px;
  background: var(--pt-gradient);
  border-radius: 8px 8px 0 0;
  overflow: hidden;
}
.feed-card-img img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
```

### C6 + C-V6 · Community feed loads everything at once — no pagination
**Files:** `app/community/routes.py`, `app/templates/community/feed.html`

```python
# In the community route, paginate:
page = request.args.get('page', 1, type=int)
recipes_page = Recipe.query.filter_by(is_deleted=False, is_public=True)\
    .order_by(Recipe.created_at.desc())\
    .paginate(page=page, per_page=12, error_out=False)
```
In `feed.html`, add a Load More button:
```html
{% if recipes_page.has_next %}
<div class="text-center mt-4">
  <a href="?page={{ recipes_page.next_num }}" class="btn btn-outline-secondary">
    Load More
  </a>
</div>
{% endif %}
```

### C10 + U10 + C-V7 · Timestamps are absolute ("Apr 22, 2026") — should be relative
**Files:** `app/templates/community/feed.html`, and notify Person C for `detail.html` comments

Add a JS relative-time helper (works without a library):
```js
function timeAgo(dateStr) {
  const diff = (Date.now() - new Date(dateStr)) / 1000;
  if (diff < 60) return 'just now';
  if (diff < 3600) return `${Math.floor(diff/60)} min ago`;
  if (diff < 86400) return `${Math.floor(diff/3600)} hr ago`;
  if (diff < 604800) return `${Math.floor(diff/86400)} days ago`;
  return new Date(dateStr).toLocaleDateString();
}
// Apply to all timestamp elements on page load:
document.querySelectorAll('[data-timestamp]').forEach(el => {
  el.textContent = timeAgo(el.dataset.timestamp);
});
```
In the template, change:
```html
<!-- From: -->
<span>{{ recipe.created_at.strftime('%b %d, %Y') }}</span>
<!-- To: -->
<span data-timestamp="{{ recipe.created_at.isoformat() }}"></span>
```
Tell Person C to apply the same `data-timestamp` pattern to comment dates in `detail.html`.

---

## 🟠 High — AI / Pantry

### G-UI-8 · "Max cooking time" input on Pantry AI does nothing
**Files:** `app/templates/ai/pantry.html`, `app/ai/services.py`

The input is shown but `get_pantry_matches()` doesn't filter by it.
```python
# In get_pantry_matches(), add a max_time parameter:
def get_pantry_matches(user_ingredients, max_time=None):
    query = Recipe.query.filter_by(is_deleted=False, is_public=True)
    if max_time:
        query = query.filter(Recipe.cooking_time <= max_time)
    # ... rest of function
```
Pass `max_time` from `ai/routes.py`:
```python
max_time = data.get('max_time')
matches = get_pantry_matches(ingredients, max_time=max_time)
```

### X-MED-2 · Pantry AI wipes user's pantry if the OpenAI call fails mid-way
**File:** `app/ai/routes.py`

The route does: DELETE all pantry → INSERT new ones → OpenAI call → `commit()`. If the OpenAI call hangs after DELETE+INSERT but before commit, the pantry is silently wiped on next load.
```python
# Commit pantry changes BEFORE the AI call:
db.session.query(PantryItem).filter_by(user_id=current_user.id).delete()
for ing in ingredients:
    db.session.add(PantryItem(user_id=current_user.id, ingredient_name=ing))
db.session.commit()  # ← commit now, before the external call

# Now make the AI call (if this fails, pantry is still saved):
suggestions = get_ai_suggestions(ingredients, ...)
```

### X-MED-3 · AI service catches all exceptions silently — users see "No suggestions"
**File:** `app/ai/services.py` (~line 79)
```python
# Replace:
except Exception:
    return []
# With:
except Exception as e:
    current_app.logger.exception('ai_suggest failed: %s', e)
    return []
```

### X-MED-4 · OpenAI prompt is vulnerable to prompt injection via `preferences`
**File:** `app/ai/services.py`

User-controlled text is directly interpolated into the system prompt:
```python
# Replace raw interpolation:
f"User preferences: {preferences or 'none'}."
# With delimited content:
f"<user_preferences>{preferences or 'none'}</user_preferences>"
# And instruct the model to treat it as data only in the system message.
```

### X-MED-5 · `get_pantry_matches` fires N+1 queries (one per recipe)
**File:** `app/ai/services.py` (~lines 20-31)
```python
# Replace per-recipe ingredient queries with a single eager load:
from sqlalchemy.orm import selectinload
recipes = Recipe.query.filter_by(is_deleted=False, is_public=True)\
    .options(selectinload(Recipe.ingredients))\
    .all()
# Now recipe.ingredients is already loaded — no extra queries in the loop
```

### C-V16 · Pantry AI shows "Finding recipes..." before user has clicked anything
**File:** `app/templates/ai/pantry.html`

The loading indicator is visible in the DOM on page load. Find the element and hide it:
```html
<div id="pantry-loading" style="display:none">
  Finding recipes…
</div>
```
Show it only when the search starts (in `pantry.js`):
```js
document.getElementById('pantry-loading').style.display = 'block';
// After results arrive:
document.getElementById('pantry-loading').style.display = 'none';
```

### D14 · `pantry.js` `renderResults()` uses raw `innerHTML` — XSS risk
**File:** `app/static/js/pantry.js`

After Person A adds `escapeHtml()` to `main.js`, use it everywhere in `pantry.js`:
```js
// Replace any instance of:
el.innerHTML = `<span>${data.title}</span>`;
// With:
el.innerHTML = `<span>${escapeHtml(data.title)}</span>`;
// Or better, use textContent:
const span = document.createElement('span');
span.textContent = data.title;
el.appendChild(span);
```

---

## 🟡 Medium — Planner backend cleanup

### G-MED-7 · Deprecated SQLAlchemy API in planner
**File:** `app/planner/routes.py` (~line 122)
```python
# Replace:
item = MealPlanItem.query.get(int(item_id))
# With:
item = db.session.get(MealPlanItem, int(item_id))
```

### X-MED-8 · `/planner` page creates a DB row on first GET request
**File:** `app/planner/routes.py` — `_get_or_create_plan()`

Visiting `/planner` for the first time silently writes a `MealPlan` row. A bot/crawler hitting the URL with a logged-in cookie would create rows.
```python
# Change _get_or_create_plan to NOT commit on GET:
def _get_or_create_plan(commit=False):
    plan = MealPlan.query.filter_by(user_id=current_user.id).first()
    if not plan:
        plan = MealPlan(user_id=current_user.id)
        db.session.add(plan)
        if commit:
            db.session.commit()
    return plan

# In the planner view route (GET): _get_or_create_plan(commit=False)
# In planner_save route (POST): _get_or_create_plan(commit=True)
```

### X-MED-9 · Soft-deleted recipes still appear in planner and grocery list
**File:** `app/planner/routes.py`

`MealPlanItem.recipe` joins without filtering `is_deleted=False`. A recipe deleted by its author still shows in other users' planners.

In the grocery list route, filter out deleted recipes:
```python
# When building the grocery list items, add:
.filter(Recipe.is_deleted == False)
```
In `planner.html`, add a fallback display:
```html
{{ item.recipe.name if item.recipe and not item.recipe.is_deleted else '(deleted recipe)' }}
```

---

## 🟡 Medium — Planner JS fixes

### D9 · Double page reload after saving to planner
**File:** `app/static/js/planner.js` (~lines 13-17)

`safeReload()` has both a `hidden.bs.modal` listener AND a `setTimeout(400)` — both can fire, causing a double reload:
```js
function safeReload() {
  modalEl.addEventListener('hidden.bs.modal', () => location.reload(), { once: true });
  modal.hide();
  // Remove the setTimeout entirely — the event listener handles it
}
```

### D16 · No `.catch` on planner remove — network failures are silent
**File:** `app/static/js/planner.js`

```js
// Find the remove fetch call and add:
.catch(err => showErrorToast('Could not remove meal. Please try again.'));
```

### D17 · Clipboard copy on grocery list has no error handling
**File:** `app/templates/planner/grocery.html`

```js
// Replace:
navigator.clipboard.writeText(text);
// With:
navigator.clipboard.writeText(text)
  .then(() => { /* optionally show "Copied!" */ })
  .catch(() => showErrorToast('Could not copy to clipboard.'));
```

### U12 · Recipe dropdown in planner assign modal is not searchable
**File:** `app/templates/planner/planner.html`

With many recipes, the `<select>` dropdown is hard to use. Add a text filter above it:
```html
<input type="text" class="form-control mb-2" id="recipeSearch"
       placeholder="Type to search recipes…"
       oninput="filterRecipeSelect(this.value)">
<select id="recipeSelect" class="form-select">…</select>

<script>
function filterRecipeSelect(query) {
  const q = query.toLowerCase();
  document.querySelectorAll('#recipeSelect option').forEach(opt => {
    opt.hidden = !opt.textContent.toLowerCase().includes(q);
  });
}
</script>
```

---

## 🔵 Low — Grocery list & print

### U16 · Print stylesheet for grocery list targets wrong CSS class
**File:** `app/templates/planner/grocery.html` or `style.css` (coordinate with Person C)

The print CSS targets `.planner-controls` which doesn't match the actual markup. Fix to properly hide the nav and controls on print:
```css
@media print {
  nav, .planner-controls, .btn, footer { display: none !important; }
  .grocery-list { font-size: 14pt; }
}
```

---

## Coordination checklist before opening your PR

- [ ] Pulled Person A's branch — `escapeHtml()`, `showErrorToast()`, `toggleFollow()` available
- [ ] All `innerHTML` in `planner.js` and `pantry.js` use `escapeHtml()` for user-supplied strings
- [ ] Told Person C: "openAddToPlanModal(recipeId, recipeName) is ready — swap the detail.html button to call it"
- [ ] Told Person C: "Add `data-timestamp` attributes to comment dates in detail.html for relative timestamps"
- [ ] Tested Day/Week toggle in the planner actually hides/shows columns
- [ ] Tested grocery list sums quantities correctly for duplicate ingredients
- [ ] No test suite regressions (`pytest tests/unit/`)
