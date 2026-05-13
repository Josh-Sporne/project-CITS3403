# Person C — Recipes & Discover
### Plate Theory · Workstream C

---

## Your role in one sentence
You own everything to do with **what a recipe looks like, how it's created, and how users find it** — including the recipe cards used throughout the entire app.

---

## Your primary files (you own these — others don't touch them)

| File | Why it's yours |
|---|---|
| `app/templates/partials/_recipe_card.html` | Recipe card partial — used on Home, Discover, Profile, Community |
| `app/templates/recipes/detail.html` | Full recipe page |
| `app/templates/recipes/create.html` | Create / edit recipe form |
| `app/templates/recipes/discover.html` | Discover page |
| `app/templates/recipes/home.html` | Home page (hero + trending sections) |
| `app/templates/recipes/my_meals.html` | My Meals tab |
| `app/static/js/discover.js` | Discover JS (currently not loaded — you'll fix this) |
| `app/static/js/validation.js` | Form validation JS (currently not loaded — you'll fix this) |
| `app/static/css/style.css` | The app's sole stylesheet |
| `app/recipes/routes.py` | Recipe-related backend routes |

---

## Shared files — how to coordinate

| File | Owner | What you need |
|---|---|---|
| `app/static/js/main.js` | **Person A** | Pull their branch before starting. You get `escapeHtml()` and `showErrorToast()` — use them wherever you'd otherwise use raw `innerHTML`. |
| `app/templates/base.html` | **Person B** | If you need a base template change, ask Person B to add it. |
| `app/models.py` | **Person A** | C14 (multi-tag) requires a schema change — coordinate with Person A to add the `RecipeTag` table. Once they merge, you do the UI part. |

**Important for the team:** `_recipe_card.html` is used on pages that belong to Person B (profile), Person D (community feed), and Person A (home/discover). When you fix the card, their pages automatically improve too — but **notify them** when you push so they can test their pages.

---

## Branch setup

```bash
# Pull Person A's branch first (requirements.txt + models.py), then:
git checkout main
git pull
git checkout -b feature/recipes-discover
```

---

## 🔴 Critical — Recipe card image fix (affects the whole app)

### B4 + U4 + C-V17 · Recipe card image goes under/over the text instead of above it
**File:** `app/templates/partials/_recipe_card.html`, `app/static/css/style.css`

**The problem:** The `<img>` is inside `<div class="img-ph">`. CSS gives `.img-ph` 100px height but `.pt-card img` forces 160px — the image overflows and clashes with the text.

**The fix — HTML (`_recipe_card.html`):**
```html
<div class="pt-card">
  {% if recipe.image_filename %}
    <img src="{{ url_for('static', filename='uploads/' + recipe.image_filename) }}"
         class="pt-card-img" alt="{{ recipe.name }}">
  {% else %}
    <div class="img-ph"></div>
  {% endif %}
  <div class="pt-card-body">
    <!-- rest of card content -->
  </div>
</div>
```

**The fix — CSS (`style.css`):**
```css
.pt-card-img {
  width: 100%;
  height: 160px;
  object-fit: cover;
  border-radius: 12px 12px 0 0;
  display: block;
}
```
This is the highest-impact fix in the codebase — it improves Home, Discover, Profile, and Community all at once.

---

## 🔴 High — Discover page JS is completely broken

### A5 + C-V11 · `discover.js` is never loaded — weaker inline version used instead
**File:** `app/templates/recipes/discover.html`, `app/static/js/discover.js`

The inline `<script>` in `discover.html` is a weaker duplicate of `discover.js`. It has no loading spinner, no error handling, no HTML escaping, and a dead `CSRF` variable.

**Fix:**
1. Delete the entire `<script>` block at the bottom of `discover.html`
2. Add at the bottom of `discover.html`:
   ```html
   {% block scripts %}
   {{ super() }}
   <script src="{{ url_for('static', filename='js/discover.js') }}"></script>
   {% endblock %}
   ```
3. Make sure `discover.js` uses `escapeHtml()` (from Person A's `main.js`) for `r.title` and `r.creator.username` in `buildCardHtml()`.

### D2 · Dead `CSRF` variable in discover inline script
This is fixed automatically when you delete the inline script in A5 above.

---

## 🔴 High — Recipe detail page problems

### G-UI-3 · No Edit/Delete buttons on the recipe detail page for the owner
**File:** `app/templates/recipes/detail.html`

If you're the creator viewing your own recipe, there are no Edit or Delete buttons — you have to navigate away to Profile or My Meals. Add a conditional block near the top action buttons:
```html
{% if current_user.is_authenticated and current_user.id == recipe.creator_id %}
<div class="d-flex gap-2 mb-3">
  <a href="{{ url_for('recipes.edit', slug=recipe.slug) }}"
     class="btn btn-sm btn-outline-secondary">
    <i class="bi bi-pencil"></i> Edit
  </a>
  <button class="btn btn-sm btn-outline-danger"
    onclick="if(confirm('Delete this recipe?')) {
      fetch('/recipe/{{ recipe.slug }}/delete', {method:'POST',
        headers:{'X-CSRFToken': document.querySelector('meta[name=csrf-token]').content}})
      .then(() => window.location.href='/')
      .catch(() => showErrorToast('Could not delete recipe.'));
    }">
    <i class="bi bi-trash"></i> Delete
  </button>
</div>
{% endif %}
```

### C11 + U5 + C-V8 · Recipe detail hero image is tiny (180px) and not expandable
**File:** `app/templates/recipes/detail.html`, `app/static/css/style.css`

**CSS fix — make it taller:**
```css
.recipe-hero-img {
  width: 100%;
  height: 300px;          /* was 180px */
  object-fit: cover;
  border-radius: 12px;
  cursor: zoom-in;
}
```

**HTML fix — make it clickable to expand:**
```html
<img src="…" class="recipe-hero-img" onclick="openImageModal(this.src)" alt="…">

<!-- Add lightbox modal: -->
<div class="modal fade" id="imgModal" tabindex="-1">
  <div class="modal-dialog modal-xl modal-dialog-centered">
    <div class="modal-content bg-transparent border-0">
      <img id="imgModalSrc" src="" class="img-fluid rounded" alt="Full size">
      <button class="btn btn-light mt-2 align-self-center"
              data-bs-dismiss="modal">Close</button>
    </div>
  </div>
</div>

<script>
function openImageModal(src) {
  document.getElementById('imgModalSrc').src = src;
  new bootstrap.Modal(document.getElementById('imgModal')).show();
}
</script>
```

### C-V19 · Comment author names are not linked to profiles
**File:** `app/templates/recipes/detail.html`

In the comments section, the `@username` is bold text but not a link:
```html
<!-- Replace: -->
<strong>@{{ comment.author.username }}</strong>
<!-- With: -->
<a href="{{ url_for('auth.public_profile', username=comment.author.username) }}"
   class="fw-bold text-decoration-none">@{{ comment.author.username }}</a>
```
Also find the JS block that appends new comments after a POST and use `escapeHtml()` from Person A's `main.js`:
```js
// Replace raw interpolation:
div.innerHTML = `<strong>@${data.comment.author}</strong>…<p>${data.comment.body}</p>`;
// With:
authorEl.href = `/user/${escapeHtml(data.comment.author)}`;
authorEl.textContent = `@${escapeHtml(data.comment.author)}`;
bodyEl.textContent = data.comment.body;  // textContent auto-escapes
```

### G-UI-6 · Star icon next to recipe count looks like a rating
**File:** `app/templates/recipes/detail.html` (~line 30)
```html
<!-- Replace: -->
<i class="bi bi-star-fill text-sun"></i> {{ recipe.creator.recipes.count() }} recipes
<!-- With: -->
<i class="bi bi-journal-text"></i> {{ recipe.creator.recipes.count() }} recipes
```

### X-LOW-9 · Recipe slug not JSON-safe in detail.html inline script
**File:** `app/templates/recipes/detail.html` (~line 129)
```js
// Replace:
const slug = '{{ recipe.slug }}';
// With:
const slug = {{ recipe.slug|tojson }};
```

### D3 · Star ratings on detail page are not keyboard-accessible
**File:** `app/templates/recipes/detail.html`
Add `tabindex` and keyboard support to the rating stars:
```html
<i class="bi bi-star-fill rating-star"
   data-score="1"
   tabindex="0"
   role="button"
   aria-label="Rate 1 star"
   onclick="submitRating(1)"
   onkeydown="if(event.key==='Enter'||event.key===' ') submitRating(1)"></i>
```
Repeat for scores 2-5.

### D6 · Comment textarea has no label — poor accessibility
**File:** `app/templates/recipes/detail.html`
```html
<label for="comment-input" class="visually-hidden">Write a comment</label>
<textarea id="comment-input" class="form-control" placeholder="Write a comment…"></textarea>
```

### U13 · No visual feedback after posting a comment or rating
**File:** `app/templates/recipes/detail.html`
- After successful comment POST: briefly add a `.highlight` CSS class to the new comment
- After successful rating: show a small "Thanks for rating!" toast using `showErrorToast()` pattern (but green version)
- Disable the comment submit button while the request is in-flight

### C3 · No rating breakdown on recipe detail
**File:** `app/templates/recipes/detail.html`, `app/recipes/routes.py`

Add a simple 1-5 star distribution bar below the average rating:
```python
# In the detail route, add:
distribution = {i: 0 for i in range(1, 6)}
for r in recipe.ratings:
    distribution[r.score] += 1
```
Render as small bars in the template.

---

## 🟠 High — Discover page

### B5 · Discover pagination ignores URL `?page=2` — always starts from page 1
**File:** `app/templates/recipes/discover.html` (or `discover.js` once loaded)

Read the initial page from the URL:
```js
let currentPage = parseInt(new URLSearchParams(window.location.search).get('page')) || 1;
```

### C-V10 · Discover category tags are missing several categories
**File:** `app/templates/recipes/discover.html`

The tag bar hardcodes only a few categories. Either:
- Pass all distinct categories from the route: `categories = db.session.query(Recipe.category).distinct().all()`
- Or dynamically generate tags in the template from that list instead of hardcoding.

### C-V12 · "Load More" button stays visible after all results are loaded
**File:** `app/templates/recipes/discover.html` (or `discover.js`)

After the `fetch` returns, check `has_next`:
```js
.then(data => {
  // ... render cards ...
  document.getElementById('load-more-btn').style.display =
    data.has_next ? 'block' : 'none';
})
```

### D4 · Discover category filter tags are `<span>` — not keyboard-focusable
**File:** `app/templates/recipes/discover.html`
```html
<!-- Replace <span class="category-tag"> with: -->
<button class="category-tag" role="button" onclick="filterByCategory(this.dataset.category)"
        data-category="breakfast">Breakfast</button>
```

### D5 · Discover search input has no label
**File:** `app/templates/recipes/discover.html`
```html
<label for="discover-search" class="visually-hidden">Search recipes</label>
<input id="discover-search" type="text" class="form-control" placeholder="Search recipes…">
```

### X-LOW-5 · `{{ total }}` interpolated as a bare JS literal
**File:** `app/templates/recipes/discover.html` (~line 76)
```js
// Replace:
let totalResults = {{ total }};
// With:
let totalResults = {{ total|tojson }};
```

---

## 🟠 High — Create/Edit recipe form

### G-UI-4 · "Remove ingredient" button clears fields but doesn't remove the row
**File:** `app/templates/recipes/create.html`

When only 1 ingredient row is left, clicking Remove clears the inputs but leaves the row — users think it's broken.
```js
function removeIngredientRow(btn) {
  const rows = document.querySelectorAll('.ingredient-row');
  if (rows.length <= 1) {
    btn.title = "Can't remove the last ingredient";
    return;
  }
  btn.closest('.ingredient-row').remove();
}
// Also disable the button when only 1 row remains:
function updateRemoveButtons() {
  const rows = document.querySelectorAll('.ingredient-row');
  rows.forEach(row => {
    const removeBtn = row.querySelector('.remove-ingredient');
    removeBtn.disabled = rows.length === 1;
  });
}
```

### D10 · Ingredient row doesn't wrap on mobile (overflows horizontally)
**File:** `app/templates/recipes/create.html`

The ingredient row is `d-flex` without `flex-wrap`. On mobile, the three inputs overflow.
```html
<!-- Change: -->
<div class="d-flex gap-2">
<!-- To: -->
<div class="d-flex flex-wrap gap-2">
```
Also set `min-width: 120px` on each input inside the row.

### A4 · `validation.js` is never loaded — form validation is dead code
**File:** `app/templates/recipes/create.html`
```html
{% block scripts %}
{{ super() }}
<script src="{{ url_for('static', filename='js/validation.js') }}"></script>
{% endblock %}
```
(Person B adds the same script tag to `register.html`.)

---

## 🟠 High — Home page

### G-UI-5 · Hero CTAs shown to unauthenticated visitors — they get bounced on click
**File:** `app/templates/recipes/home.html` (lines 16-25)

"Create Recipe", "Plan This Week", and "Try Pantry AI" all require login but are shown to everyone.
```html
{% if current_user.is_authenticated %}
  <a href="{{ url_for('recipes.create') }}" class="btn btn-mint">Create Recipe</a>
  <a href="{{ url_for('planner.planner') }}" class="btn btn-outline-light">Plan This Week</a>
  <a href="{{ url_for('ai.pantry') }}" class="btn btn-outline-light">Try Pantry AI</a>
{% else %}
  <a href="{{ url_for('auth.register') }}" class="btn btn-mint btn-lg">Sign up — it's free</a>
  <a href="{{ url_for('auth.login') }}" class="btn btn-outline-light">Log in</a>
{% endif %}
```

---

## 🟡 Medium — Recipes

### C4 + U9 · Category badges are plain text — clicking them does nothing
**Files:** `app/templates/partials/_recipe_card.html`, `app/templates/recipes/detail.html`

```html
<!-- Replace plain badge: -->
<span class="badge bg-secondary">{{ recipe.category }}</span>
<!-- With a link: -->
<a href="{{ url_for('recipes.discover') }}?category={{ recipe.category|lower }}"
   class="badge bg-secondary text-decoration-none">{{ recipe.category }}</a>
```

### C5 · "New This Week" shows all-time newest, not actually this week
**File:** `app/recipes/routes.py` (~line 33)
```python
from datetime import datetime, timedelta
one_week_ago = datetime.utcnow() - timedelta(days=7)
new_recipes = Recipe.query.filter(
    Recipe.created_at >= one_week_ago,
    Recipe.is_deleted == False,
    Recipe.is_public == True
).order_by(Recipe.created_at.desc()).limit(3).all()
```

### G-MED-2 · Recipe privacy (`is_public`) not surfaced in create/edit form
**File:** `app/templates/recipes/create.html`, `app/recipes/routes.py`

`Recipe.is_public` exists in the model but there's no UI toggle to set it. Users can't create private recipes.
```html
<div class="form-check mb-3">
  <input class="form-check-input" type="checkbox" name="is_public"
         id="is_public" checked>
  <label class="form-check-label" for="is_public">
    Make this recipe public (visible to everyone on Discover)
  </label>
</div>
```
In the route: `recipe.is_public = 'is_public' in request.form`

### G-MED-3 · No Follow button on recipe cards — users have to navigate away to follow
**File:** `app/templates/partials/_recipe_card.html`

Add a small follow button next to the creator's name:
```html
{% if current_user.is_authenticated and current_user.id != recipe.creator_id %}
<button class="btn btn-sm btn-outline-secondary ms-1 follow-btn"
  data-username="{{ recipe.creator.username }}"
  data-following="{{ 'true' if current_user.is_following(recipe.creator) else 'false' }}"
  onclick="toggleFollow(this.dataset.username, this)">
  {{ 'Following' if current_user.is_following(recipe.creator) else '+ Follow' }}
</button>
{% endif %}
```

### D11 · My Meals page shows soft-deleted recipes
**File:** `app/recipes/routes.py` — `my_meals` route (~line 390)
```python
# Replace:
Recipe.query.filter_by(creator_id=current_user.id)
# With:
Recipe.query.filter_by(creator_id=current_user.id, is_deleted=False)
```

### G-UI-10 · My Meals page shows no recipe images
**File:** `app/templates/recipes/my_meals.html`

Cards are text-only. Add the same conditional image block used in the profile recipe tab:
```html
{% if recipe.image_filename %}
  <img src="{{ url_for('static', filename='uploads/' + recipe.image_filename) }}"
       class="pt-card-img" alt="{{ recipe.name }}">
{% else %}
  <div class="img-ph"></div>
{% endif %}
```

### C-V20 · Stars on recipe cards look interactive but aren't
**Files:** `app/templates/partials/_recipe_card.html`, `app/static/css/style.css`

Add a tooltip showing the actual value so users understand they're display-only:
```html
<span title="Average rating: {{ recipe.avg_rating|round(1) }}"
      aria-label="Average rating: {{ recipe.avg_rating|round(1) }} out of 5">
  {% for i in range(1, 6) %}
    <i class="bi bi-star{% if i <= recipe.avg_rating %}-fill{% endif %} text-sun small"></i>
  {% endfor %}
</span>
```
In CSS, remove any `cursor: pointer` on `.pt-card .bi-star-fill`.

---

## 🔵 Low — Multi-tag support (coordinate with Person A first)

### C14 · Only one category per recipe — no multi-tag support
**Dependency:** Person A must add the `RecipeTag` / `Tag` table to `models.py` and run migrations first. Once that's merged:

**Your part — `create.html`:**
Replace the single `<select name="category">` with a chip/multi-select input:
```html
<div class="mb-3">
  <label class="form-label">Tags</label>
  <div id="tag-chips" class="d-flex flex-wrap gap-2">
    {% for tag in available_tags %}
    <input type="checkbox" class="btn-check" name="tags" value="{{ tag.id }}"
           id="tag-{{ tag.id }}" autocomplete="off">
    <label class="btn btn-sm btn-outline-secondary" for="tag-{{ tag.id }}">
      {{ tag.name }}
    </label>
    {% endfor %}
  </div>
</div>
```

**Your part — `discover.html`:**
Update the category filter to support multiple selected tags (filter by "has any of these tags").

---

## 🔵 Low — CSS & Polish

### D12 · Many unused CSS classes in `style.css`
**File:** `app/static/css/style.css`

Safe to remove (search the codebase first to confirm none are used):
`.panel`, `.board-item`, `.stat-box`, `.pill-btn`, `.skeleton`, `.animate-slide-down`, `.gap-grid`, `.font-heading`, `.rounded-pt`, `.glow-mint`, `.glow-coral`, `.bg-surface`, `.bg-surface2`, `.bg-dark-custom`, `.border-mint`, `.border-subtle`, `.grid-cards-3`, `.two-col`

### G-MED-4 · Footer background doesn't change with dark/light theme toggle
**File:** `app/static/css/style.css`

Find the `footer` style and change to use CSS variables:
```css
footer {
  background: var(--pt-surface);
  color: var(--pt-text);
  border-top: 1px solid var(--pt-border);
}
```

### U17 · "Share recipe" button — copy link to clipboard
**File:** `app/templates/recipes/detail.html`
```html
<button class="btn btn-sm btn-outline-secondary"
  onclick="navigator.clipboard.writeText(window.location.href)
    .then(() => this.textContent = 'Copied!')
    .catch(() => showErrorToast('Could not copy link.'))">
  <i class="bi bi-share"></i> Share
</button>
```

### U19 · Skeleton loading cards (CSS class exists, never used)
**File:** `app/templates/recipes/discover.html`

While cards are loading (before the fetch resolves), show skeleton placeholder cards:
```js
function showSkeletons(count = 4) {
  const grid = document.getElementById('recipe-grid');
  for (let i = 0; i < count; i++) {
    const el = document.createElement('div');
    el.className = 'pt-card skeleton';
    el.style.height = '260px';
    grid.appendChild(el);
  }
}
```
Call `showSkeletons()` before the fetch, then clear them when results arrive.

---

## Coordination checklist before opening your PR

- [ ] Pulled Person A's branch — `escapeHtml()` and `showErrorToast()` available in `main.js`
- [ ] All `innerHTML` in your scripts use `escapeHtml()` for user-supplied data
- [ ] Recipe card image fix tested on Home, Discover, and Profile pages (which use `_recipe_card.html`)
- [ ] Notified team: "_recipe_card.html has been updated — pull and test your pages"
- [ ] `style.css` changes don't break Person B's profile styles (test `/profile` after your changes)
- [ ] C14 (multi-tag) only done after Person A merges the schema change
