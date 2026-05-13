# Person A — Security & Backend Hardening
### Plate Theory · Workstream A

---

## Your role in one sentence
You fix everything that can **crash the server, corrupt the database, or be exploited** — and you go first, because your changes unlock the rest of the team.

---

## Your primary files (you own these — others don't touch them)

| File | Why it's yours |
|---|---|
| `requirements.txt` | Missing packages that break a fresh install |
| `app/models.py` | Schema integrity, nullable fields, slug logic |
| `app/__init__.py` | Error handlers, security headers |
| `app/static/js/main.js` | Global JS helpers (`escapeHtml`, `toggleFollow`, `.catch` patterns) |
| `app/auth/forms.py` | Username/email validators |

You will also make **small, localised validation edits** inside route files — a 2-3 line `try/except` or a type check per function. These don't conflict with the feature work others are doing in the same files because they touch different functions.

---

## Shared files — how to coordinate

| File | Owner | What you need from them / they need from you |
|---|---|---|
| `app/static/js/main.js` | **You** | After you add `escapeHtml()` and `toggleFollow()`, ping the team. B, C, and D each need to call these helpers in their templates instead of raw `innerHTML`. |
| `app/auth/routes.py` | **Person B** | You only touch lines 23, 40-41 (redirect fixes + open redirect). Person B adds new routes/features. Coordinate so you don't edit the same function. |

---

## Branch setup

```bash
git checkout main
git pull
git checkout -b feature/security-backend
```

When done: open a PR into `dev` (or `main` if no dev branch). **Merge this before anyone else opens their PR** — your `requirements.txt` and `models.py` changes need to be in `main` first.

---

## ⚡ Do these FIRST (others are blocked on them)

### DEP-1 · Add `python-slugify` to `requirements.txt`
**File:** `requirements.txt`
Anyone doing a fresh `pip install -r requirements.txt` gets an `ImportError` on startup because `models.py` imports `slugify`.
```
python-slugify==8.0.4
```

### DEP-2 · Add `python-dotenv` to `requirements.txt`
**File:** `requirements.txt`
`config.py` does `from dotenv import load_dotenv` — same crash on a clean install.
```
python-dotenv==1.0.1
```

### DEP-3 · Add `openai` to `requirements.txt`
**File:** `requirements.txt`
Currently in a `try` block so server starts, but teammates' AI features silently fail.
```
openai>=1.0.0
```

---

## 🔴 Critical — Security

### X-CRIT-2 · Add `escapeHtml` helper to `main.js` (stored XSS fix — step 1 of 2)
**File:** `app/static/js/main.js`
Raw `innerHTML` with user data is used in 5 places across the codebase. Your job is to add the helper function. Persons B, C, D will replace their `innerHTML` calls with it.

Add this to the top of `main.js`:
```js
function escapeHtml(s) {
  const d = document.createElement('div');
  d.appendChild(document.createTextNode(s ?? ''));
  return d.innerHTML;
}
window.escapeHtml = escapeHtml; // make globally accessible
```
Then notify the team: "escapeHtml is now available globally — replace `${data.comment.body}` etc. with `${escapeHtml(data.comment.body)}`."

### X-CRIT-3 · Username case collision (account impersonation)
**File:** `app/auth/forms.py`
`filter_by(username=field.data)` is case-sensitive. Registering `ALICE` after `alice` succeeds, giving two accounts with the same name.
```python
# In validate_username(), replace:
if User.query.filter_by(username=field.data).first():

# With:
if User.query.filter(
    func.lower(User.username) == field.data.lower()
).first():
    raise ValidationError('Username already taken.')
# Also strip and lowercase before saving:
field.data = field.data.strip().lower()
```
Apply the same case-insensitive lookup in `auth/routes.py` login query and `public_profile` lookup.

### X-CRIT-4 · Email case collision (two accounts share an email)
**File:** `app/auth/forms.py`
Same root cause as X-CRIT-3 but on email.
```python
# In validate_email():
field.data = field.data.strip().lower()
if User.query.filter(
    func.lower(User.email) == field.data
).first():
    raise ValidationError('Email already registered.')
```

### X-CRIT-5 · IDOR on planner save — private recipe titles leak via ID guessing
**File:** `app/planner/routes.py` (around line 91)
`item.recipe_id = int(recipe_id)` with no check. Posting another user's private recipe ID returns 200 and renders that recipe's title in the user's planner.
```python
if recipe_id:
    try:
        rid = int(recipe_id)
    except (ValueError, TypeError):
        return jsonify(success=False, error='Invalid recipe_id'), 400
    r = Recipe.query.filter_by(id=rid, is_deleted=False).first()
    if r is None or (not r.is_public and r.creator_id != current_user.id):
        return jsonify(success=False, error='Recipe not found'), 400
    item.recipe_id = r.id
```
Also add at app startup (`app/__init__.py` or the SQLAlchemy event):
```python
@event.listens_for(engine, 'connect')
def set_sqlite_pragma(conn, _):
    conn.execute('PRAGMA foreign_keys=ON')
```

### C12 · Open redirect on `/login` — `?next=` can redirect to any URL
**File:** `app/auth/routes.py` (lines 40-41)
```python
# Replace:
next_page = request.args.get('next')
return redirect(next_page or '/')

# With:
from urllib.parse import urlparse
nxt = request.args.get('next')
if nxt:
    parsed = urlparse(nxt)
    if parsed.netloc or parsed.scheme:
        nxt = None
return redirect(nxt or url_for('recipes.home'))
```

---

## 🟠 High — Server crashes (500 errors from bad input)

Each of these is 1-3 lines in a route function. None conflict with the feature work others are adding.

### X-HIGH-1 · `POST /recipe/<slug>/comment` crashes on non-string body
**File:** `app/recipes/routes.py` (~line 341)
```python
# Replace:
body = (data.get('body') or '').strip()
# With:
body = str(data.get('body') or '').strip()
```

### X-HIGH-2 · `POST /api/planner/save` crashes on non-numeric `day`
**File:** `app/planner/routes.py` (~line 75)
```python
# After the `day is None` check, add:
try:
    day = int(day)
except (ValueError, TypeError):
    return jsonify(success=False, error='Invalid day'), 400
```

### X-HIGH-5 · `/recipe/<slug>/rate` accepts Python `True` as a valid 1-star rating
**File:** `app/recipes/routes.py` (~line 308)
```python
# Replace:
if not isinstance(score, int) or score < 1 or score > 5:
# With:
if not isinstance(score, int) or isinstance(score, bool) or score < 1 or score > 5:
```

### X-HIGH-6 · No length limit on comments (50k-char comment was accepted)
**File:** `app/recipes/routes.py` (comment route)
```python
if len(body) > 2000:
    return jsonify(success=False, error='Comment too long (max 2000 chars)'), 400
```
Also in `app/planner/routes.py` (planner save, custom_text):
```python
if custom_text and len(custom_text) > 200:
    custom_text = custom_text[:200]
```

### X-HIGH-7 · `/api/recipes` accepts unbounded `per_page` — dumps entire DB
**File:** `app/recipes/routes.py` (~line 77)
```python
per_page = request.args.get('per_page', 12, type=int)
page = request.args.get('page', 1, type=int)
# Add after:
per_page = max(1, min(per_page, 50))
page = max(1, page)
```

### X-HIGH-8 · Pantry suggest accepts a string for `ingredients` — trashes DB with single characters
**File:** `app/ai/routes.py` (~line 33)
```python
ingredients = data.get('ingredients', [])
if not isinstance(ingredients, list):
    return jsonify(success=False, error='ingredients must be a list'), 400
```

### X-HIGH-9 · Username allows HTML and whitespace
**File:** `app/auth/forms.py`
```python
from wtforms.validators import Regexp
# Add to username field validators:
Regexp(r'^[A-Za-z0-9_\-]{3,80}$', message='Username can only contain letters, numbers, - and _')
```

---

## 🟡 Medium — Code quality & integrity

### G-MED-6 · Symbol-only recipe title (e.g. `!!!`) produces a 404 slug
**File:** `app/models.py` — `generate_slug()` method
```python
# After slug = slugify(self.title):
if not slug or slug.strip('-') == '':
    slug = f'recipe-{self.id or "new"}'
```

### G-MED-8 · Hardcoded `redirect('/')` in auth routes
**File:** `app/auth/routes.py` (lines 23, 41, 50)
```python
# Replace all instances of:
return redirect('/')
# With:
return redirect(url_for('recipes.home'))
```

### G-MED-9 · `User.email` exposed in leaderboard query
**File:** `app/community/routes.py` (~line 49)
Remove `User.email` from the `group_by` and `select` in the leaderboard query.

### X-LOW-10 · `MealPlan` and `MealPlanItem` FK columns not `nullable=False`
**File:** `app/models.py`
```python
# MealPlan:
user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
# MealPlanItem:
mealplan_id = db.Column(db.Integer, db.ForeignKey('meal_plan.id', ondelete='CASCADE'), nullable=False)
```
After editing, run: `flask db migrate -m "nullable FK constraints"` and `flask db upgrade`.

### X-LOW-15 · `Recipe.generate_slug` hits DB once per retry (O(n))
**File:** `app/models.py`
```python
# Replace the while loop with:
base = slugify(self.title) or 'recipe'
existing = {r.slug for r in Recipe.query.filter(
    Recipe.slug.like(f'{base}%')
).with_entities(Recipe.slug).all()}
slug = base
counter = 1
while slug in existing:
    slug = f'{base}-{counter}'
    counter += 1
self.slug = slug
```

---

## 🟡 Global JS — helpers the whole team uses

### B7/U11 · Add `.catch` error toast helper to `main.js`
**File:** `app/static/js/main.js`
Add a shared helper so everyone can handle fetch failures consistently:
```js
function showErrorToast(message) {
  // If you have Bootstrap toasts set up, use that.
  // Simple fallback:
  const el = document.createElement('div');
  el.className = 'alert alert-danger position-fixed bottom-0 end-0 m-3';
  el.style.zIndex = 9999;
  el.textContent = message;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 4000);
}
window.showErrorToast = showErrorToast;
```
Notify team to add `.catch(err => showErrorToast('Something went wrong. Please try again.'))` to their fetch chains.

### X-LOW-8 · Extract `toggleFollow` into `main.js` (shared by B and D)
**File:** `app/static/js/main.js`
```js
function toggleFollow(username, btn) {
  const isFollowing = btn.dataset.following === 'true';
  fetch(`/user/${username}/follow`, {
    method: 'POST',
    headers: { 'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content }
  })
  .then(r => r.json())
  .then(data => {
    if (data.success) {
      btn.dataset.following = !isFollowing;
      btn.textContent = isFollowing ? 'Follow' : 'Unfollow';
    }
  })
  .catch(() => showErrorToast('Could not update follow status.'));
}
window.toggleFollow = toggleFollow;
```

### D1 · `confirmAction()` references a non-existent modal
**File:** `app/static/js/main.js`
`confirmAction()` tries to show `#confirmModal` which doesn't exist in any template, so it falls back to `window.confirm()`. Either build the modal in `base.html` (coordinate with Person B) or remove the dead reference and always use `window.confirm()` until a modal is built.

---

## 🔵 Low — Cleanup

### X-LOW-12 · Extract `_json_body()` helper (used in 6 routes)
Create `app/utils.py` (new file):
```python
from flask import request

def json_body():
    data = request.get_json(silent=True)
    if data is None:
        from flask import current_app
        current_app.logger.debug('json_body: missing or malformed JSON body')
        return {}
    return data
```
Then in each route replace `request.get_json(silent=True) or {}` with `json_body()`.

### X-LOW-13 · No error page for oversized file uploads (413)
**File:** `app/__init__.py`
```python
@app.errorhandler(413)
def file_too_large(e):
    flash('File too large — maximum size is 4 MB.', 'danger')
    return redirect(request.referrer or url_for('recipes.create')), 413
```

### X-LOW-16 · No HTTP security headers
**File:** `app/__init__.py`
```python
@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    # Add CSP once XSS (X-CRIT-2) is fully fixed:
    # response.headers['Content-Security-Policy'] = "default-src 'self'; ..."
    return response
```

### D13 · Delete dead files
These files are never imported and confuse teammates:
- `app/forms.py`
- `app/routes.py`
- `app/planner/forms.py`
- `app/static/style.css` (root-level duplicate)
- `templates/.gitkeep`
- `fruit.py`, `test.py`, `test2.py`

```bash
git rm app/forms.py app/routes.py app/planner/forms.py app/static/style.css fruit.py test.py test2.py templates/.gitkeep
```

### D18 · Selenium test fails due to missing CSRF token
**File:** `tests/selenium/test_flows.py` — `test_create_recipe_flow`
The test enables CSRF but doesn't include the token in the form submission. Disable CSRF in the test config, or extract and submit the CSRF token from the page.

### D19 · Selenium test fails on re-runs (unique username constraint)
**File:** `tests/selenium/test_flows.py` — `test_register_flow`
```python
# Replace fixed username:
username = f'testuser_{int(time.time())}'
```

---

## Coordination checklist before opening your PR

- [ ] `requirements.txt` has all 3 packages added
- [ ] `flask db migrate` and `flask db upgrade` run cleanly after `models.py` changes
- [ ] `escapeHtml` and `showErrorToast` and `toggleFollow` are in `main.js` and work
- [ ] Told the team: "Pull my branch — `escapeHtml()`, `showErrorToast()`, `toggleFollow()` are now global. Please use them in your templates."
- [ ] No test suite regressions (`pytest tests/unit/`)
