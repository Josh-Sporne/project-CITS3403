# Person B — Auth & Profiles
### Plate Theory · Workstream B

---

## Your role in one sentence
You own everything to do with **users** — how they log in, what their profile looks like, who they follow, and how others see them.

---

## Your primary files (you own these — others don't touch them)

| File | Why it's yours |
|---|---|
| `app/templates/auth/login.html` | Login page theming fix |
| `app/templates/auth/register.html` | Register page theming fix |
| `app/templates/auth/profile.html` | Profile page — all tabs, settings, saved |
| `app/templates/auth/public_profile.html` | Other users' profiles |
| `app/templates/base.html` | Nav, footer, theme toggle, active page indicator |
| `app/auth/routes.py` | New profile routes, follow/unfollow, avatar upload, user search |
| `app/auth/forms.py` | New form fields (password, avatar) — Person A handles validators |

---

## Shared files — how to coordinate

| File | Owner | What you need |
|---|---|---|
| `app/static/css/style.css` | **Person C** | If you need new CSS for profile components, add a `/* PERSON B */` comment block at the bottom and tell Person C so they can integrate it into the stylesheet properly. |
| `app/static/js/main.js` | **Person A** | After Person A merges, pull their branch. You get `escapeHtml()`, `showErrorToast()`, and `toggleFollow()` for free — use them in your template scripts. |
| `app/auth/routes.py` | **Shared (you + A)** | Person A touches lines 23, 40-41 only (redirect fixes). You add new route functions. Don't edit the same functions. |

---

## Branch setup

```bash
# Wait for Person A to merge their requirements.txt + models.py changes first, then:
git checkout main
git pull
git checkout -b feature/auth-profiles
```

---

## 🔴 Critical — Fix follow/unfollow (currently crashes with 405)

### A1 + A2 · Follow/Unfollow on public profile returns "Method Not Allowed"
**File:** `app/templates/auth/public_profile.html` (lines 20-28)

The page uses `<a href="…/follow">` which is a GET request, but the backend only accepts POST. This is why clicking Follow does nothing.

Replace the `<a>` links with a button that uses `fetch` POST (same pattern as `feed.html`):
```html
{% if current_user.is_authenticated and current_user.id != profile_user.id %}
<button
  class="btn btn-sm btn-mint follow-btn"
  data-username="{{ profile_user.username }}"
  data-following="{{ 'true' if current_user.is_following(profile_user) else 'false' }}"
  onclick="toggleFollow(this.dataset.username, this)">
  {{ 'Unfollow' if current_user.is_following(profile_user) else 'Follow' }}
</button>
{% endif %}
```
`toggleFollow()` is provided by Person A in `main.js` — make sure you've pulled their branch before testing.

---

## 🔴 Critical — Login/Register stuck in dark mode

### G-UI-1 · Login and Register pages are hard-coded dark
**Files:** `app/templates/auth/login.html`, `app/templates/auth/register.html`

Both templates use `class="card bg-dark border-secondary"` and `btn-primary`. When a user switches to light mode, these two pages stay dark while every other page goes light.

- Replace `bg-dark border-secondary` with `pt-panel` (the CSS-variable-aware class already in `style.css`)
- Replace all `btn-primary` on these pages with `btn-mint`
- Also remove any hardcoded `color: white` inline styles

---

## 🔴 High — Profile page issues

### B1 + U8 · No way to unsave a recipe from the Saved tab
**File:** `app/templates/auth/profile.html` (Saved tab section)

The Saved tab only shows "View Recipe". To unsave, users have to navigate to the recipe page. The toggle endpoint `POST /recipe/<slug>/save` already exists.

Add a small unsave button to each saved recipe card:
```html
<button
  class="btn btn-sm btn-outline-secondary"
  onclick="fetch('/recipe/{{ recipe.slug }}/save', {
    method: 'POST',
    headers: {'X-CSRFToken': document.querySelector('meta[name=csrf-token]').content}
  }).then(() => this.closest('.saved-card').remove())
  .catch(() => showErrorToast('Could not unsave recipe.'))">
  <i class="bi bi-bookmark-x"></i> Unsave
</button>
```

### B8 · Profile edit silently swallows validation errors
**File:** `app/auth/routes.py` — `profile_edit` route

If `EditProfileForm` fails validation, it currently redirects to the profile page with no error shown. The user has no idea what went wrong.
```python
# Replace silent redirect with:
if not form.validate_on_submit():
    for field, errors in form.errors.items():
        for error in errors:
            flash(f'{field}: {error}', 'danger')
    return redirect(url_for('auth.profile'))
```

### G-UI-7 · Profile buttons use Bootstrap blue instead of mint-green
**File:** `app/templates/auth/profile.html` (lines 116, 157, 185)

Three `btn-primary` buttons break the mint-green scheme used everywhere else.
- Replace all `btn-primary` in `profile.html` with `btn-mint`

---

## 🟠 High — Public profile overhaul

### C8 + U3 + C-V3 · Public profile looks like a completely different app
**File:** `app/templates/auth/public_profile.html`

Own profile: green avatar, large stat tiles, styled recipe cards.
Public profile: tiny avatar, inline text stats, dark Bootstrap cards.

Reuse the same structure from `profile.html`:
- Copy the `profile-header` section (avatar, username, bio, stat tiles)
- Show the same four stat tiles: Recipes, Avg Rating, Followers, Following
- Use `profile-recipe-card` instead of `card bg-dark` for recipe listings
- Hide the Settings tab and Edit buttons for non-owners:
  ```html
  {% if current_user.is_authenticated and current_user.id == profile_user.id %}
    <!-- settings tab here -->
  {% endif %}
  ```

### C7 · Public profile missing "Following" count
**File:** `app/auth/routes.py` — `public_profile()` route, and `public_profile.html`

The route doesn't pass `following_count` to the template.
```python
# In public_profile() route, add to the render_template call:
following_count=profile_user.following.count()
```
Then display it alongside the other stats in the template.

### C-V4 · Public profile recipe cards are dark grey in light mode
**File:** `app/templates/auth/public_profile.html`

Cards use `card bg-dark` — this looks broken in light mode. After you restyle using the profile.html components (C8 above), this is automatically fixed.

### G-MED-1 · Dark mode shows black (unreadable) text on public profile
**File:** `app/templates/auth/public_profile.html`

Some text uses Bootstrap's `text-muted` class which ignores the app's custom dark mode CSS variables.
- Replace every `text-muted` with `text-muted-custom` throughout `public_profile.html`

### C9 · Public profile only shows recipes — no tabs for engagement
**File:** `app/templates/auth/public_profile.html`, `app/auth/routes.py`

Add tabs like the own-profile page:
- **Recipes** tab (already there)
- **Ratings Given** tab — show a list of recipes this user has rated, with their score
- **Comments** tab — show a list of this user's comments with a link to the recipe

In the route, pass the extra data:
```python
ratings = Rating.query.filter_by(user_id=profile_user.id).order_by(Rating.id.desc()).limit(20).all()
comments = Comment.query.filter_by(author_id=profile_user.id).order_by(Comment.created_at.desc()).limit(20).all()
```

---

## 🟠 High — Followers / Following modal

### C1 + U2 + C-V14 · Follower/Following counts are not clickable
**Files:** `app/templates/auth/profile.html`, `app/auth/routes.py`

The "7 FOLLOWERS" and "4 FOLLOWING" stat tiles do nothing on click.

**Step 1 — Add a modal to `profile.html`:**
```html
<div class="modal fade" id="followModal" tabindex="-1">
  <div class="modal-dialog">
    <div class="modal-content pt-panel">
      <div class="modal-header">
        <h5 class="modal-title" id="followModalTitle">Followers</h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
      </div>
      <div class="modal-body" id="followModalBody">
        <!-- populated by JS -->
      </div>
    </div>
  </div>
</div>
```

**Step 2 — Make the stat tiles clickable:**
```html
<div class="profile-stat" style="cursor:pointer"
     onclick="openFollowModal('followers')">
  <div class="stat-number">{{ followers_count }}</div>
  <div class="stat-label">FOLLOWERS</div>
</div>
```

**Step 3 — Add API endpoints to `auth/routes.py`:**
```python
@auth.route('/api/followers/<username>')
@login_required
def api_followers(username):
    user = User.query.filter_by(username=username).first_or_404()
    followers = [f.follower for f in user.followers]
    return jsonify([{
        'username': u.username,
        'avatar_url': u.avatar_url,
        'is_following': current_user.is_following(u)
    } for u in followers])
```
(Repeat for `/api/following/<username>`)

**Step 4 — JS to populate and open the modal:**
```js
function openFollowModal(type) {
  const username = '{{ current_user.username }}';
  fetch(`/api/${type}/${username}`)
    .then(r => r.json())
    .then(users => {
      document.getElementById('followModalTitle').textContent =
        type === 'followers' ? 'Followers' : 'Following';
      document.getElementById('followModalBody').innerHTML =
        users.map(u => `
          <div class="d-flex align-items-center mb-3">
            <img src="${escapeHtml(u.avatar_url)}" class="rounded-circle me-2" width="36">
            <a href="/user/${escapeHtml(u.username)}" class="me-auto">${escapeHtml(u.username)}</a>
            <button class="btn btn-sm btn-mint"
              data-username="${escapeHtml(u.username)}"
              data-following="${u.is_following}"
              onclick="toggleFollow(this.dataset.username, this)">
              ${u.is_following ? 'Unfollow' : 'Follow'}
            </button>
          </div>`).join('');
      new bootstrap.Modal(document.getElementById('followModal')).show();
    })
    .catch(() => showErrorToast('Could not load list.'));
}
```

---

## 🟡 Medium — Account settings

### C2 · Can't edit username, email, or password
**Files:** `app/templates/auth/profile.html` (Settings tab), `app/auth/routes.py`, `app/auth/forms.py`

The Settings tab currently only shows a bio field.

Add to the Settings form in `profile.html`:
- A "Change Username" input (pre-filled with current username)
- A "Change Email" input
- A "New Password" + "Confirm Password" pair

Add to `auth/forms.py`:
```python
class EditProfileForm(FlaskForm):
    bio = TextAreaField('Bio', validators=[Length(max=500)])
    new_username = StringField('New Username', validators=[Optional(), Length(3, 80)])
    new_email = EmailField('New Email', validators=[Optional(), Email()])
    new_password = PasswordField('New Password', validators=[Optional(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password',
        validators=[Optional(), EqualTo('new_password')])
```

Handle in `profile_edit` route — only update fields that are non-empty.

### C15 + U20 · Profile picture is fixed (Gravatar) — can't upload a custom photo
**Files:** `app/templates/auth/profile.html` (Settings tab), `app/auth/routes.py`

Add a file upload field in the Settings tab:
```html
<input type="file" name="avatar" accept="image/*" class="form-control mb-2">
```

In the route:
```python
avatar_file = request.files.get('avatar')
if avatar_file and avatar_file.filename:
    filename = secure_filename(f'avatar_{current_user.id}_{avatar_file.filename}')
    avatar_file.save(os.path.join(app.config['UPLOAD_FOLDER'], 'avatars', filename))
    current_user.avatar_url = url_for('static', filename=f'uploads/avatars/{filename}')
```
Create `app/static/uploads/avatars/` directory (add a `.gitkeep`).
Update `User.avatar_url` in `models.py` to be a regular `String` column instead of a property.

### C16 · No way to search for other users
**Files:** New template (e.g. `templates/auth/directory.html`), `app/auth/routes.py`

Add a `/community/users` page with a search box:
```python
@auth.route('/users')
def user_directory():
    q = request.args.get('q', '').strip()
    users = []
    if q:
        users = User.query.filter(
            User.username.ilike(f'%{q}%')
        ).limit(20).all()
    return render_template('auth/directory.html', users=users, query=q)
```
Also add a search icon to the navbar in `base.html` that links to `/users`.

---

## 🟡 Medium — `base.html` improvements

### G-MED-5 · Browser back button causes light/dark theme flash
**File:** `app/templates/base.html`

The back-forward cache restores the page without re-running the theme script. Add a `pageshow` listener:
```js
// In base.html <script> block, after the existing theme init:
window.addEventListener('pageshow', function(e) {
  const theme = localStorage.getItem('theme') || 'dark';
  document.documentElement.setAttribute('data-theme', theme);
});
```

### C-V18 · Hamburger menu doesn't show which page is active
**File:** `app/templates/base.html`

Add the Bootstrap `active` class dynamically:
```html
<a class="nav-link {% if request.endpoint == 'recipes.home' %}active{% endif %}"
   href="{{ url_for('recipes.home') }}">Home</a>
```
Repeat for each nav link using the correct `request.endpoint` value.

### G-LOW-1 · Footer year is hard-coded (will break Jan 2027)
**File:** `app/templates/base.html` + `app/__init__.py`

In `app/__init__.py`, add a context processor:
```python
from datetime import datetime

@app.context_processor
def inject_year():
    return {'current_year': datetime.utcnow().year}
```
In `base.html`, replace the hard-coded year:
```html
Plate Theory © {{ current_year }} | CITS3403 Group Project
```

### X-MED-6 · Profile tab URL hash injected unsafely into CSS selector
**File:** `app/templates/auth/profile.html` (the Bootstrap tab JS block)

Find where `window.location.hash` is used in a `querySelector` call and add validation:
```js
const hash = window.location.hash;
if (hash && /^#[a-z\-]{1,32}$/i.test(hash)) {
  const tab = document.querySelector(`[data-bs-target="${hash}"]`);
  if (tab) bootstrap.Tab.getOrCreateInstance(tab).show();
}
```

### A4 · `validation.js` is never loaded
**File:** `app/templates/auth/register.html` (and note for Person C to add it to `create.html`)

Add at the bottom of `register.html`:
```html
{% block scripts %}
{{ super() }}
<script src="{{ url_for('static', filename='js/validation.js') }}"></script>
{% endblock %}
```

---

## 🔵 Low — Accessibility & Polish

### D7 · Delete button on profile has no `aria-label`
**File:** `app/templates/auth/profile.html`
```html
<!-- Replace: -->
<button class="btn btn-sm btn-danger"><i class="bi bi-trash"></i></button>
<!-- With: -->
<button class="btn btn-sm btn-danger" aria-label="Delete recipe">
  <i class="bi bi-trash"></i>
</button>
```

---

## Coordination checklist before opening your PR

- [ ] Pulled Person A's branch — `toggleFollow()`, `escapeHtml()`, `showErrorToast()` are available
- [ ] All `innerHTML` in your scripts use `escapeHtml()` for user-supplied strings
- [ ] New avatar upload directory `app/static/uploads/avatars/` exists (with `.gitkeep`)
- [ ] If you added any new CSS, you put it in a block at the bottom of `style.css` (coordinate with Person C)
- [ ] `flask db migrate` and `flask db upgrade` run cleanly if you changed `models.py`
- [ ] Told Person D: "`toggleFollow()` is in `main.js` — use it in `feed.html` too"
