# Plate Theory — Full Product Audit & UX Improvement Plan

> Generated: April 22, 2026
> Covers every template, JS file, CSS rule, route handler, and model in the app.

---

## Status Legend

- [ ] Not started
- [~] In progress
- [x] Complete

---

## PART A: BUGS & BROKEN FEATURES

### 1. Critical — Broken on click

- [ ] **A1 · Follow/Unfollow returns 405 on public profile**
  `public_profile.html` lines 20-28 use `<a href="…">` (GET), but `/user/<username>/follow` is POST-only. The community feed does it correctly with `fetch` POST.
  **Fix:** Replace the `<a>` tags with a JS `fetch` POST button, same pattern as `feed.html`.

- [ ] **A2 · Follow URL is constructed oddly**
  URL is `url_for('auth.public_profile', username=…)/follow` — this concatenation accidentally produces the correct path, but the GET method is the real blocker.
  **Fix:** Addressed by A1 (switch to fetch POST).

- [ ] **A3 · Day/Week toggle does NOT change the planner view**
  The Day/Week buttons only switch the grocery preview API call (`?range=day`). The 7-day grid always renders all 7 days regardless of which button is active. Users expect "Day" to show only today's column.
  **Fix:** In `planner.js`, hide/show day columns based on `currentRange`. When "Day" is active, show only today's `day-slot`; when "Week", show all 7.

- [ ] **A4 · `validation.js` is never loaded**
  No template includes `<script src="…/validation.js">`. Client-side validation for register and recipe-create forms is fully written but dead code.
  **Fix:** Add `<script>` tag to `base.html` or to the specific templates that need it (`register.html`, `create.html`).

- [ ] **A5 · `discover.js` is never loaded — weaker inline duplicate used instead**
  `discover.html` has an inline script that duplicates `discover.js` but is weaker: no loading spinner, no error handling, no HTML escaping, and a dead `CSRF` variable.
  **Fix:** Either load the better `discover.js` in the template's `{% block scripts %}` and remove the inline script, or merge `discover.js`'s improvements (spinner, escaping, error handling) into the inline version.

---

### 2. High — Feature exists in UI but doesn't work properly

- [ ] **B1 · No unsave button in Saved tab**
  `profile.html` Saved tab only shows "View Recipe" — no way to unsave. The toggle endpoint `POST /recipe/<slug>/save` already exists.
  **Fix:** Add a bookmark-x icon button that calls the save-toggle endpoint.

- [ ] **B2 · "Add to Meal Plan" doesn't pass recipe context**
  `detail.html` line 42 links to `/planner` generically. User lands on the empty planner with no idea which recipe they wanted to add.
  **Fix:** Link to `/planner?recipe_id=<id>` and have `planner.js` auto-open the assign modal with that recipe pre-selected, or show a mini-modal directly on the detail page.

- [ ] **B3 · Clicking a meal in the planner doesn't show the recipe**
  Meals show recipe titles as plain text (`<span class="slot-content">`). Clicking "Masala Omelette" on Tuesday breakfast does nothing.
  **Fix:** Wrap recipe titles in a link to `/recipe/<slug>`, or add a click handler that opens a recipe-preview modal.

- [ ] **B4 · Recipe card image overflows its wrapper (wrong positioning)**
  In `_recipe_card.html`, the `<img>` is nested inside `<div class="img-ph">`. CSS sets `.img-ph` to 100px height but `.pt-card img` forces 160px → image overflows or is clipped by `overflow: hidden`. The image appears to go under/over the text rather than sitting cleanly above it.
  **Fix:** Remove the `<img>` from inside `.img-ph`. Render the image as a direct child of `.pt-card` when it exists; only show the gradient `.img-ph` placeholder when there's no image.

- [ ] **B5 · Discover pagination desyncs on direct URL**
  Inline JS always starts `currentPage = 1`. Visiting `?page=2` directly is ignored.
  **Fix:** Read `page` from `URLSearchParams` on init.

- [ ] **B6 · Grocery list joins quantities as strings**
  Shows "2, 3" instead of summing to "5" when the same ingredient appears in multiple meals.
  **Fix:** Parse numeric quantities and sum them in the aggregation logic.

- [ ] **B7 · No `.catch` on most `fetch` calls — silent failures**
  Rating, comment, save, follow, and discover API calls fail silently on network errors. User gets zero feedback.
  **Fix:** Add `.catch` with user-visible error toasts/alerts to all `fetch` chains.

- [ ] **B8 · `profile_edit` silently swallows validation errors**
  `auth/routes.py` — if `EditProfileForm` doesn't validate, it redirects to profile without any flash message or error display.
  **Fix:** Flash validation errors before redirect, or re-render the form with errors.

---

### 3. Medium — Missing expected features

- [ ] **C1 · No followers/following list**
  Stat numbers on profile are not clickable. Users expect to see who they follow and who follows them.
  **Fix:** Add a modal that lists users with avatar, username, profile link, and follow/unfollow button.

- [ ] **C2 · Can't edit username, email, or password**
  Settings tab only has bio. Basic account management is missing.
  **Fix:** Add form fields and backend routes for username, email, and password changes.

- [ ] **C3 · No rating breakdown on recipe detail**
  Only shows average + count. No per-score distribution or list of who rated.
  **Fix:** Add a small bar chart showing 1-5 star distribution.

- [ ] **C4 · Category badges not clickable**
  Badges ("Breakfast", "Italian", etc.) on recipe cards and detail page are plain text.
  **Fix:** Wrap badges in `<a href="/discover?category=…">`.

- [ ] **C5 · "New This Week" has no date filter**
  Shows latest 3 recipes regardless of when they were created.
  **Fix:** Filter by `created_at >= now - 7 days` in the query.

- [ ] **C6 · No pagination on community feed, profile tabs, or my-meals**
  Everything loads all records at once. Will degrade with growth.
  **Fix:** Add paginated API endpoints or "load more" buttons.

- [ ] **C7 · Public profile missing "Following" count**
  Only shows followers + recipe count, unlike the logged-in profile which shows all four stats.
  **Fix:** Pass `following_count` from `public_profile()` route and display it.

- [ ] **C8 · Public profile uses completely different styling from own profile**
  Own profile: `profile-header`, `profile-stat` tiles, `profile-recipe-card`.
  Public profile: generic Bootstrap `card bg-dark`, inline styles.
  Feels like two different apps.
  **Fix:** Reuse the same profile components, just hide edit/settings for non-owners.

- [ ] **C9 · No way to view others' ratings, comments, or community activity**
  Public profile only shows their recipes. No tabs for engagement.
  **Fix:** Add "Ratings given" and "Comments" tabs to the public profile.

- [ ] **C10 · Comments use absolute timestamps**
  Shows "Mar 11, 2026" instead of "2 hours ago".
  **Fix:** Use a relative time helper (JS `Intl.RelativeTimeFormat` or Jinja `timeago` filter).

- [ ] **C11 · Recipe detail image is not expandable**
  Hero image is fixed 180px with `object-fit: cover`. No lightbox or zoom.
  **Fix:** Add click-to-expand modal showing the full-resolution image.

- [ ] **C12 · Open redirect vulnerability on login**
  `?next=` parameter is not validated in `auth/routes.py`. Could redirect to external URLs.
  **Fix:** Validate that `next` is a relative URL before redirecting.

- [ ] **C13 · Leaderboard "Top Creators This Month" has no month filter**
  Query returns all-time data despite the heading.
  **Fix:** Filter leaderboard query by `created_at` in current month.

- [ ] **C14 · Only one category per recipe — no multi-tag support**
  `Recipe.category` is a single `String(50)` column (`models.py`). A recipe cannot be both **vegan** and **halal**, or tagged for **lunch** and **dinner** at once. Discover filters assume one category per row.
  **Fix:** Add a `RecipeTag` (or `Tag`) many-to-many table, or a JSON array column; update create/edit forms to multi-select or chip input; update discover and API to filter by “has all selected tags” or “has any”.

- [ ] **C15 · Profile picture is fixed (Gravatar) — cannot upload a custom avatar**
  `User.avatar_url` is derived from email (Gravatar/identicon). Settings has no file upload; there is no route to store `uploads/avatars/…`.
  **Fix:** Optional image upload on profile settings, store filename on `User`, serve like recipe images. (Also listed as **U20** in Tier 3.)

- [ ] **C16 · No user discovery — cannot search or browse people “like Instagram”**
  You **can** open another user’s page if you already have their username (`GET /user/<username>` from recipe bylines, community feed, leaderboard). There is **no** global user search, no “suggested users”, no followers list to browse from, and public profiles lack depth (stats, tabs, activity) compared to a typical social profile.
  **Fix:** Add `/community/directory` or search endpoint + UI; optional `@handle`-style search in nav; enrich public profile (C8, C9, C7, C1) so visiting someone feels complete.

- [ ] **C17 · Meal planner Day vs Week (re-stated)**
  Same as **A3**: the Day/Week control only changes grocery preview range; the calendar grid never switches to a single-day layout.
  **Fix:** See **A3** / **U6** / Phase 1 item 3.

---

### 4. Low — Polish & cleanup

- [ ] **D1 · `confirmAction()` in `main.js` references non-existent `confirmModal`**
  Falls back to `window.confirm()` which works, but the intended styled modal doesn't exist.

- [ ] **D2 · Dead `CSRF` variable in discover inline script**
  Declared but never used (GET-only page).

- [ ] **D3 · Star ratings on detail page are mouse-only**
  `<i>` tags with `click` listener — no `tabindex`, no `role="button"`, no keyboard support.

- [ ] **D4 · Discover category tags are `<span>` not `<button>`**
  Not keyboard-focusable, no `role="button"` or `tabindex`.

- [ ] **D5 · Discover search input has no `<label>`**
  Only has `placeholder` — poor accessibility.

- [ ] **D6 · Comment textarea has no `<label>`**
  `detail.html` — only has `placeholder`.

- [ ] **D7 · Icon-only buttons missing `aria-label`**
  Delete button on profile, remove `×` button on planner.

- [ ] **D8 · Grocery checkbox IDs use raw ingredient names**
  Spaces, unicode, or quotes in names produce invalid or duplicate DOM IDs.

- [ ] **D9 · Double reload after planner save**
  `planner.js` fires reload on both `modal hidden` event and a `setTimeout(400)`. Race condition can cause double page load.

- [ ] **D10 · Ingredient row on create page doesn't wrap on mobile**
  `d-flex` without `flex-wrap` — three inputs overflow horizontally on narrow screens.

- [ ] **D11 · `my_meals` lists soft-deleted recipes alongside active ones**
  Query has no `is_deleted=False` filter (may be intentional to show "deleted" state, but confusing).

- [ ] **D12 · Many unused CSS classes in `style.css`**
  `.panel`, `.board-item`, `.stat-box`, `.pill-btn`, `.skeleton`, `.animate-slide-down`, `.gap-grid`, `.font-heading`, `.rounded-pt`, `.glow-mint`, `.glow-coral`, `.bg-surface`, `.bg-surface2`, `.bg-dark-custom`, `.border-mint`, `.border-subtle`, `.grid-cards-3`, `.two-col`.

- [ ] **D13 · Dead files to clean up**
  `app/forms.py`, `app/routes.py`, `app/planner/forms.py`, `app/static/style.css` (old duplicate), `templates/.gitkeep`, `fruit.py`, `test.py`, `test2.py`.

- [ ] **D14 · XSS risk in `pantry.js` `renderResults`**
  Injects API response strings into HTML without escaping. `discover.js` has `escapeHtml` but `pantry.js` does not.

- [ ] **D15 · `planner_save` can 500 on non-integer `recipe_id`**
  `int(recipe_id)` raises `ValueError` with no handler.

- [ ] **D16 · No `.catch` on planner remove**
  `planner.js` — network failure silently ignored.

- [ ] **D17 · Clipboard copy has no error handling**
  `grocery.html` — `navigator.clipboard.writeText` can fail on non-HTTPS or denied permission.

- [ ] **D18 · Selenium `test_create_recipe_flow` fails with CSRF**
  Test enables CSRF but doesn't submit the token.

- [ ] **D19 · Selenium `test_register_flow` fails on re-runs**
  Fixed username `newuser` hits unique constraint if DB persists.

---

## PART B: UX IMPROVEMENT SUGGESTIONS

### Tier 1 — High-impact interactions

- [ ] **U1 · Recipe modal from meal planner**
  Clicking a recipe name in a planner slot (e.g., "Masala Omelette" on Tuesday morning) should open a modal showing: recipe image, ingredients, cooking time, rating, and a "View Full Recipe" link. This is the single most natural interaction users will attempt.

- [ ] **U2 · Followers/Following modals on profile**
  Clicking the "Followers" or "Following" stat number should pop a modal listing each user with their avatar, username, link to their profile, and an inline follow/unfollow button.

- [ ] **U3 · Rich public profiles (match own-profile styling)**
  Public profiles should use the same `profile-header` + stat tiles + recipe cards as the own-profile page. Add tabs: Recipes, Ratings, Comments. Show "Following" count. Make visiting someone's profile feel rewarding.

- [ ] **U4 · Fix recipe card image to sit cleanly above text**
  Remove the `.img-ph` wrapper when a real image exists. Image should render as a direct child of `.pt-card` with the gradient placeholder only shown when no image is available.

- [ ] **U5 · Expandable recipe detail image (lightbox)**
  Click the 180px hero image → opens a modal overlay with the full-resolution image and a close button. Simple CSS/JS, no library needed.

- [ ] **U6 · Working Day view in planner**
  When "Day" is selected, show only today's column expanded with taller slots and more detail. When "Week" is selected, show the compact 7-day grid. Make it feel like a real calendar toggle.

### Tier 2 — Medium-impact enhancements

- [ ] **U7 · "Add to Meal Plan" with recipe context**
  From recipe detail, "Add to Meal Plan" should open a mini-modal: pick a day + meal type → save directly. No navigation away from the recipe.

- [ ] **U8 · Unsave button on saved recipes**
  In the profile Saved tab, each card should have a bookmark-x icon that toggles unsave with a single click (the toggle endpoint already exists).

- [ ] **U9 · Clickable category badges everywhere**
  Tapping "Breakfast" on any recipe card or detail page navigates to `/discover?category=breakfast` with that filter pre-applied.

- [ ] **U10 · Relative timestamps ("2 hours ago")**
  Replace absolute dates on comments and feed items with relative times.

- [ ] **U11 · Loading states and error feedback on all interactions**
  Every `fetch` call should show a spinner/disabled state on the triggering button and display a toast/alert on failure. Currently most fail silently.

- [ ] **U12 · Searchable recipe dropdown in planner modal**
  The "Choose a recipe" `<select>` in the assign modal should be searchable (type to filter). With many recipes, scrolling a raw dropdown is painful.

- [ ] **U13 · Smooth comment/rating feedback**
  After posting a comment, briefly highlight the new entry. After rating, show "Thanks for rating!" toast. Disable the comment button while submitting.

### Tier 3 — Nice-to-have polish

- [ ] **U14 · Recipe card hover preview**
  On desktop, hovering a card shows a subtle tooltip with the description and extra info.

- [ ] **U15 · Drag-and-drop in planner**
  Allow dragging recipes from a sidebar into planner slots as an alternative to the modal.

- [ ] **U16 · Fix print stylesheet for grocery list**
  The print CSS targets `.planner-controls` which doesn't match the actual markup. Fix it to properly hide controls and format the list.

- [ ] **U17 · "Share recipe" button**
  Copy-to-clipboard link sharing on the recipe detail page.

- [ ] **U18 · Empty state illustrations**
  Replace plain-text empty states with illustrated SVGs or meaningful icons.

- [ ] **U19 · Skeleton loading cards**
  CSS class `.skeleton` exists but is unused. Apply it for discover/feed loading states.

- [ ] **U20 · Profile avatar upload**
  Same scope as **C15** — Gravatar-only today; add optional upload in Settings + storage + `avatar_url` override.

- [ ] **U21 · Notification dot on Community nav**
  Show an unread indicator when followed users post new recipes.

- [ ] **U22 · Recipe delete confirmation modal**
  Replace browser `confirm()` with a styled Bootstrap modal matching the app design.

---

## PART C: VISUAL & LAYOUT ISSUES (Found via browser testing)

> Issues found by running the app at `http://127.0.0.1:5001` and inspecting every page in a browser (April 22, 2026).
> Each item includes what page, what the problem looks like, and what should happen instead.

### C-V1 · Footer says "© 2025" — should be 2026

- **Page:** Every page (rendered from `base.html`).
- **What it looks like:** Footer reads "Plate Theory © 2025 | CITS3403 Group Project".
- **Should be:** "© 2026" or dynamically `{{ now.year }}`.

### C-V2 · Planner grid cuts off Saturday and Sunday columns

- **Page:** `/planner`
- **What it looks like:** At typical laptop viewport widths (~1024px), the 7-column grid shows Monday through Friday clearly, but Saturday is partially visible (cut off mid-word "Satu…") and Sunday is hidden behind the scroll. There's no visual cue that more columns exist — no scroll indicator or arrow.
- **Should be:** Either show a horizontal scroll indicator/arrow, auto-scroll to today, or make the grid responsive enough to show all 7 days without truncation (e.g. narrower slots).

### C-V3 · Public profile looks completely different from own profile

- **Page:** `/user/josh` vs `/profile`
- **What it looks like:** Own profile has a beautiful green-bordered circular avatar, large stat tiles (Recipes, Avg Rating, Followers, Following), styled `profile-recipe-card` cards. Public profile has a plain small round avatar, inline text stats ("3 followers 5 recipes"), dark grey `card bg-dark` recipe cards.
- **Should be:** Both pages should share the same profile header component and card style. The public profile should feel like viewing someone else's version of your own profile page.

### C-V4 · Public profile recipe cards use dark-grey background in light mode

- **Page:** `/user/josh`
- **What it looks like:** Recipe cards use `card bg-dark` Bootstrap class with `bg-secondary` placeholder areas. In light mode, these dark cards look jarring and inconsistent with the rest of the app's light card style.
- **Should be:** Use `profile-recipe-card` or `pt-card` components that respect the light/dark theme.

### C-V5 · Grocery list shows string-concatenated quantities ("basil 1, 1 handful")

- **Page:** `/grocery`
- **What it looks like:** When the same ingredient appears in multiple recipes, quantities are joined as strings: "basil 1, 1 handful" instead of being summed or intelligently merged.
- **Should be:** Numeric quantities summed ("basil 2"); mixed unit quantities shown as "basil — 1 + 1 handful" or similar.

### C-V6 · Community feed has no pagination — all 25+ recipes load at once

- **Page:** `/community`
- **What it looks like:** All recipes from all users load in a single massive scroll. With 32 recipes and the leaderboard sidebar, this is a very long page.
- **Should be:** Paginated or infinite-scroll with "Load more", similar to discover.

### C-V7 · Community feed timestamps are absolute ("Apr 22, 2026")

- **Page:** `/community`
- **What it looks like:** Each recipe post says "Apr 22, 2026" — all the same date since they were seeded together.
- **Should be:** Relative timestamps ("2 hours ago", "yesterday"). Matches the same issue on comments (C10).

### C-V8 · Recipe detail hero image is very short (180px) and crops heavily

- **Page:** `/recipe/garlic-butter-noodles`
- **What it looks like:** The hero image is forced to 180px height with `object-fit: cover`. For a food photo, this aggressive crop hides most of the dish. The image cannot be clicked to expand.
- **Should be:** Taller hero (280-320px minimum), and clicking should open a full-resolution lightbox/modal.

### C-V9 · Recipe detail "Add to Meal Plan" goes to generic planner with no context

- **Page:** `/recipe/garlic-butter-noodles`
- **What it looks like:** Clicking "Add to Meal Plan" navigates away from the recipe to `/planner`. The planner has no idea which recipe the user wanted to add.
- **Should be:** Open a mini-modal on the recipe page: "Add Garlic Butter Noodles to: [Day dropdown] [Meal dropdown] [Save]". No navigation needed.

### C-V10 · Discover category tags are missing several categories

- **Page:** `/discover`
- **What it looks like:** Tags show: All, Breakfast, Lunch, Dinner, Snack, Dessert, Vegan. But the system has recipes in categories like "High-protein", "Vegetarian", "One-pot", "Quick-meals" that are not in the tag bar.
- **Should be:** Either dynamically generate tags from all categories in the DB, or add the missing ones.

### C-V11 · Discover has no loading indicator when fetching results

- **Page:** `/discover`
- **What it looks like:** When clicking a category filter or "Load More", there's no spinner, skeleton, or loading text. The page just sits there until results appear (or silently fails on network error).
- **Should be:** Show a spinner or skeleton cards while loading. The external `discover.js` file has this logic but is never loaded.

### C-V12 · Discover page "Load More" button stays visible even after all recipes are loaded

- **Page:** `/discover`
- **What it looks like:** After clicking "Load More" enough times to exhaust all 32 recipes, the button stays. Clicking it again either shows nothing or duplicates cards.
- **Should be:** Hide the button when `has_next` is `false`.

### C-V13 · Planner meal names are not clickable — plain text only

- **Page:** `/planner`
- **What it looks like:** "Masala Omelette" in Tuesday breakfast, "Garlic Butter Noodles" in Tuesday lunch — all just `<span>` text. No link, no click handler, no hover effect.
- **Should be:** Clicking a meal name should either link to the recipe detail page or open a modal preview showing the recipe image, ingredients, rating.

### C-V14 · Profile stat numbers (Followers / Following) are not clickable

- **Page:** `/profile`
- **What it looks like:** "7 FOLLOWERS" and "4 FOLLOWING" are static styled divs. Cursor doesn't change on hover. No click behavior.
- **Should be:** Clicking opens a modal listing the follower/following users with profile links and follow/unfollow buttons.

### C-V15 · Saved recipes tab has no unsave action

- **Page:** `/profile` → Saved tab
- **What it looks like:** Each saved recipe card only has "View Recipe" button. To unsave, users must navigate to the full recipe detail page and toggle save there.
- **Should be:** An unsave icon (bookmark-x) on each saved card.

### C-V16 · Pantry AI shows "Finding recipes..." text by default

- **Page:** `/pantry`
- **What it looks like:** The "Finding recipes..." loading text or spinner appears even before the user has clicked "Find Matching Recipes". It seems the element is visible in the DOM on page load.
- **Should be:** Hidden by default, shown only when a search is in progress.

### C-V17 · No recipe images in Trending or New This Week on Home

- **Page:** `/`
- **What it looks like:** All recipe cards on the home page show gradient placeholders, even for the one recipe that has an uploaded image (Garlic Butter Noodles). This is because Garlic Butter Noodles isn't in the trending or new queries, but if it were, the `_recipe_card.html` partial would have the image-inside-`.img-ph` layout bug.
- **Should be:** Fix the `_recipe_card.html` partial to render images above text cleanly (see B4).

### C-V18 · Navbar hamburger menu doesn't show active page indicator

- **Page:** Every page
- **What it looks like:** On mobile (collapsed nav), the hamburger menu shows all links but none is highlighted to indicate which page the user is currently on.
- **Should be:** Active page link should be visually distinct (bold, underlined, different color).

### C-V19 · Comment author names are not linked to profiles

- **Page:** `/recipe/garlic-butter-noodles` → Comments section
- **What it looks like:** "@josh" in the comment is styled as bold text but is NOT a link. Users can't click a commenter's name to visit their profile.
- **Should be:** Wrap `@username` in an `<a href="/user/username">` link.

### C-V20 · Stars on recipe cards are display-only but look interactive

- **Page:** Home, Discover, Profile recipe cards
- **What it looks like:** Stars (★★★★☆) are shown with gold fill, which looks like they might be clickable for rating. They're purely decorative display of the average.
- **Should be:** Either add a tooltip "Average rating: 4.5" or make them slightly smaller/muted to look less interactive.

### C-V21 · Leaderboard says "This Month" but includes all-time data

- **Page:** `/community` sidebar
- **What it looks like:** "Top Creators This Month" heading, but the query returns all-time recipe counts. If the seeded data has recipes from months ago, they'd all count.
- **Should be:** Filter by `created_at` in the current month.

---

## PART D: RECOMMENDED IMPLEMENTATION ORDER

### Phase 1 — Fix what's broken (this week)

1. A1 — Fix follow button on public profile (POST fetch)
2. B4/U4/C-V17 — Fix recipe card image positioning (`_recipe_card.html`)
3. A3/C-V2/U6 — Make Day/Week toggle change the planner view + fix column cutoff
4. B3/U1/C-V13 — Make planner meals clickable (recipe modal)
5. A4+A5/C-V11 — Load `validation.js`, consolidate discover JS, add loading states
6. B1/U8/C-V15 — Add unsave button in Saved tab
7. B7/U11 — Add `.catch` + loading states to all fetch calls
8. C-V1 — Fix footer year (2025 → dynamic)
9. C-V5/B6 — Fix grocery quantity string concatenation
10. C-V12 — Hide "Load More" when no more results

### Phase 2 — Missing features (next sprint)

1. C-V3/C-V4/C8/U3 — Unify public/private profile styling
2. C1/U2/C-V14 — Followers/Following modal
3. C11/U5/C-V8 — Expandable recipe images + taller hero
4. U7/B2/C-V9 — "Add to Meal Plan" with context (modal on recipe page)
5. C-V10 — Add missing category tags to discover
6. C4/U9 — Clickable category badges everywhere
7. C-V19 — Link commenter names to profiles
8. C10/U10/C-V7 — Relative timestamps
9. C2 — Editable username/email/password
10. C12 — Fix open redirect vulnerability
11. C-V6 — Add pagination to community feed
12. C-V21/C13 — Fix leaderboard month filter
13. **C14** — Multi-tag recipes (schema + forms + discover filters)
14. **C15/U20** — Custom profile photo upload
15. **C16** — User search / directory + richer public profiles (with C8, C9, C1)

### Phase 3 — Polish (later)

1. C-V16 — Fix pantry AI loading state default
2. C-V18 — Active page indicator in navbar
3. C-V20 — Distinguish decorative stars from interactive ones
4. U12-U22 — Tier 3 enhancements
5. D1-D19 — All low-priority cleanup
6. Dead file removal (D13)
7. Unused CSS cleanup (D12)
8. Accessibility fixes (D3-D7)

---

## PART E: FILES REFERENCE

| Area | Key files |
|------|-----------|
| Templates | `app/templates/` (17 files across auth/, recipes/, planner/, ai/, community/, partials/) |
| JavaScript | `app/static/js/` — `main.js`, `planner.js`, `pantry.js`, `discover.js` (unused), `validation.js` (unused) |
| CSS | `app/static/css/style.css` (sole stylesheet, ~1550 lines) |
| Routes | `app/auth/routes.py`, `app/recipes/routes.py`, `app/planner/routes.py`, `app/ai/routes.py`, `app/community/routes.py` |
| Models | `app/models.py` (User, Recipe, RecipeIngredient, MealPlan, MealPlanItem, Rating, Comment, SavedRecipe, PantryItem, Follower) |
| Config | `config.py`, `.env`, `.env.example` |
| Tests | `tests/unit/` (4 files), `tests/selenium/` (1 file) |

---

## PART F: Additional backlog (team / user requests)

Short notes from follow-up review; each item maps to a tracked ID above.

| Request | Status in app | Tracked as |
|--------|----------------|------------|
| Multiple tags per recipe (e.g. vegan **and** halal; lunch **and** dinner) | Single `category` string only | **C14** |
| Day / Week on planner — Day should change the view | UI toggles but grid stays 7 days | **A3**, **C17**, **U6**, Phase 1 #3 |
| Profile picture feels default — want to change it | Gravatar/identicon only | **C15**, **U20**, Phase 2 #14 |
| Find other users / stats “like Instagram” | Profiles exist at `/user/<username>` but no search, no directory, thin public profile | **C16** (+ **C8**, **C9**, **C1**, **C7**) |

---

## PART G: Items already fixed (verified in source)

These were tracked in earlier audit passes but are **already correct** in the current codebase — mark complete and remove from sprint work:

- [x] **C-V1 — Footer year "© 2025"** — `base.html` already reads "© 2026". Still hard-coded (see G-LOW-1), but the year is correct right now.
- [x] **C13 / C-V21 — Leaderboard "This Month" includes all-time data** — `community/routes.py` already filters by `Recipe.created_at >= month_start`. Correct.

---

## PART H: New findings from group-mate reviews

> Sources: `CITS3403 Group Project Bugs.pdf`, `CITS3403 Group Project Additional Bugs.pdf`, `site.docx`
> Every item below was cross-checked against the existing AUDIT.md before adding — nothing here is a duplicate.

---

### H-CRIT — Critical: Security & Data Integrity

- [ ] **X-CRIT-2 · Stored XSS via `innerHTML` across 5 files**
  `detail.html` comment-append path builds HTML with raw template-literal interpolation:
  ```js
  div.innerHTML = `<strong>@${data.comment.author}</strong>…<p>${data.comment.body}</p>`;
  ```
  The server stores comment bodies verbatim — a body of `<img src=x onerror=alert(1)>` is accepted (`200`), saved, and **executes for every subsequent visitor** (stored XSS, not reflected). The same unescaped-`innerHTML` pattern exists in: `pantry.js` (AI result titles / chip names), `planner.js` (grocery preview ingredient names), `grocery.html` (full list), and `discover.html` inline `buildCardHtml()`.
  Since ingredients come from `/recipe/create`, a recipe author can plant XSS that fires in any other user's planner or grocery list.
  **Fix:** Promote the `escapeHtml()` helper already in `discover.js:164` into `main.js`; apply it in all five files. Use `textContent` or `createElement`/`appendChild` instead of `innerHTML` where possible.
  *(D14 in existing audit flags `pantry.js` as "XSS risk" but misses the stored-XSS severity and the four other affected files.)*

- [ ] **X-CRIT-3 · Username case collision allows account impersonation**
  `auth/forms.py` validates uniqueness with `filter_by(username=field.data)` — case-sensitive on SQLite. Registering `ALICE` after `alice` succeeds; both accounts exist, both log in, and `@ALICE` comments appear alongside `@alice` comments.
  **Fix:** Normalize to lowercase on save; check `func.lower(User.username) == username.lower()`; add a DB-level unique index on `lower(username)`.

- [ ] **X-CRIT-4 · Email case collision lets two accounts share an email**
  Same root cause as X-CRIT-3 on the email field (`auth/forms.py:35-37`). `alice@example.com` and `ALICE@example.com` can both be registered. Critical for any future account-recovery flow.
  **Fix:** Lowercase emails on input in a custom validator; mirror to all "find user by email" lookups.

- [ ] **X-CRIT-5 · IDOR via unvalidated `recipe_id` on planner save**
  `planner/routes.py:91-92` sets `item.recipe_id = int(recipe_id)` with no existence or visibility check. Posting `{recipe_id: 99999}` writes an orphan row (`200`). Worse: posting the ID of another user's **private** recipe causes the planner to render that recipe's title — a read of private data via guessed IDs. SQLite FK enforcement is off, so the orphan survives.
  **Fix:** Look up the recipe, assert `is_deleted=False` and `(is_public or creator_id == current_user.id)` before assigning. Enable `PRAGMA foreign_keys=ON`.
  *(D15 tracks only the `ValueError` 500; the IDOR aspect is new.)*

---

### H-CRIT-DEPS — Critical: Missing Dependencies (app won't start on a clean install)

- [ ] **G-DEP-1 · `python-slugify` missing from `requirements.txt`**
  `models.py:6` does `from slugify import slugify`. A fresh `pip install -r requirements.txt` skips this → `ImportError` on startup.

- [ ] **G-DEP-2 · `python-dotenv` missing from `requirements.txt`**
  `config.py:2` does `from dotenv import load_dotenv`. Same startup crash on a clean install.

- [ ] **G-DEP-3 · `openai` missing from `requirements.txt`**
  `ai/services.py` imports it inside a `try` block so the server starts, but teammates don't get it on `pip install` and AI features silently fail.

---

### H-HIGH — High: 500 Errors from Missing Input Validation

- [ ] **X-HIGH-1 · `POST /recipe/<slug>/comment` 500s on non-string body**
  `routes.py:341`: `body = (data.get('body') or '').strip()` — if client sends `{"body": 123}`, `.strip()` raises `AttributeError`. Verified live: status 500.
  **Fix:** `body = str(data.get('body') or '').strip()`

- [ ] **X-HIGH-2 · `POST /api/planner/save` 500s on non-numeric `day`**
  Guard checks `day is None` but not type. Sending `{"day": "monday"}` passes and crashes `int()`. Verified live: 500 `ValueError`.
  **Fix:** Wrap `int()` in `try/except ValueError`, return 400.

- [ ] **X-HIGH-5 · `POST /recipe/<slug>/rate` accepts Python `True` as a valid score**
  `isinstance(True, int)` is `True` in Python, so `{"score": true}` passes the 1-5 guard and is stored as `score=1`. Verified live.
  **Fix:** `isinstance(score, int) and not isinstance(score, bool)`.

- [ ] **X-HIGH-6 · No server-side length cap on comments or custom meal text**
  A 50,000-character comment was accepted live (status 200). `MealPlanItem.custom_text` is `String(200)` in schema but the route doesn't enforce it — SQLite silently truncates, Postgres would 500.
  **Fix:** Add `Length(max=2000)` to comment validation; enforce `len(custom_text) <= 200` in `planner_save`.

- [ ] **X-HIGH-7 · `/api/recipes` accepts unbounded `per_page`**
  `?per_page=999999` returns the entire recipe table. `?page=-1` is accepted (SQLite treats negative offsets as 0; Postgres does not).
  **Fix:** `per_page = max(1, min(per_page, 50))` and `page = max(1, page)`.

- [ ] **X-HIGH-8 · Pantry suggest 200s when `ingredients` is a string**
  `ai/routes.py:33` — if a client sends `"garlic,onion"` (string instead of array), Python iterates characters and writes `PantryItem(name='g')`, `'a'`… to the DB silently.
  **Fix:** `if not isinstance(ingredients, list): return jsonify(success=False, error='ingredients must be array'), 400`

- [ ] **X-HIGH-9 · Username allows leading/trailing whitespace and raw HTML**
  `RegisterForm.username` only enforces `Length(min=3, max=80)`. `' spaced '` and `<script>alert(1)</script>` are saved verbatim. The HTML doesn't fire in Jinja (autoescaped), but it **does** fire through the `innerHTML` paths in X-CRIT-2 (e.g. `@${data.comment.author}`).
  **Fix:** Add `Regexp(r'^[A-Za-z0-9_\-]{3,80}$')` validator; strip whitespace before validation.

---

### H-HIGH-UI — High: Confirmed UI Bugs (from Bugs.pdf)

- [ ] **G-UI-1 · Login and Register pages hard-coded dark — break light theme**
  `login.html` and `register.html` use `class="card bg-dark border-secondary"` and `btn-primary`. Switching to light mode leaves these two pages dark; the blue button also clashes with the mint-green scheme.
  **Fix:** Replace `bg-dark` with `pt-panel`/`auth-card` and `btn-primary` with `btn-mint`.

- [ ] **G-UI-2 · Community feed image height is inconsistent**
  `feed.html:53-58` — a recipe **with** an image renders a bare `<img>` (no fixed height); a recipe **without** an image renders `<div class="img-ph">` (fixed 100px). Cards in the feed are different heights.
  **Fix:** Always wrap the image in the same container with a fixed height, matching the fix for B4.

- [ ] **G-UI-3 · No Edit / Delete buttons on recipe detail page for the owner**
  `detail.html` — the recipe creator has no way to edit or delete from the detail page. They must navigate away to Profile or My Meals.
  **Fix:** Add a conditional block for `current_user.id == recipe.creator_id` showing Edit and Delete buttons next to the Save / Add-to-Plan buttons.

- [ ] **G-UI-4 · "Remove ingredient" button clears fields but doesn't remove the row**
  `create.html` — when only 1 ingredient row remains, Remove clears the inputs but leaves the row. Users think the button is broken.
  **Fix:** Disable the Remove button (or show a tooltip "Can't remove the last ingredient") when `rowCount == 1`.

- [ ] **G-UI-5 · Home hero CTAs shown to unauthenticated users who then get bounced**
  `home.html:16-25` — "Create Recipe", "Plan This Week", "Try Pantry AI" require login but are shown to all visitors. Clicking any bounces the user to `/login`.
  **Fix:** Wrap in `{% if current_user.is_authenticated %}` or swap to a "Sign up to get started" CTA for guests.

- [ ] **G-UI-6 · Star icon next to recipe count on detail page looks like a rating**
  `detail.html:30`: `<i class="bi bi-star-fill text-sun"></i> {{ recipe.creator.recipes.count() }} recipes` — a gold star next to a number reads as a rating, not a count.
  **Fix:** Use `bi-journal` or `bi-book` icon.

- [ ] **G-UI-7 · Profile page uses Bootstrap blue (`btn-primary`) — breaks mint-green scheme**
  `profile.html` lines 116, 157, 185 use `btn-primary` on "Save Changes" and empty-state CTAs. Every other CTA uses `btn-mint`.
  **Fix:** Replace with `btn-mint`.

- [ ] **G-UI-8 · Pantry AI "Max cooking time" input has no effect on results**
  The input is shown in `pantry.html` but `ai/services.py:get_pantry_matches()` does not filter by cooking time. Users set it and see no difference.
  **Fix:** Add `.filter(Recipe.cooking_time <= max_time)` to the matches query, or remove the input.

- [ ] **G-UI-9 · Community follow check fires N+1 DB queries per feed render**
  `feed.html:34`: `current_user.is_following(recipe.creator)` runs a DB query per recipe card (up to 30+ queries per page load).
  **Fix:** Pre-fetch the set of followed user IDs in the route; pass as a Python set to the template; check with `recipe.creator_id in followed_ids`.

- [ ] **G-UI-10 · My Meals page does not render recipe images**
  `my_meals.html` uses text-only cards. Even recipes with uploaded images show no thumbnail.
  **Fix:** Add the same conditional image block used in `profile.html` recipe cards.

---

### H-MED — Medium: UX, Integrity & Code Quality

- [ ] **G-MED-1 · Public profile dark mode has unreadable black text**
  On `/user/<username>` in dark mode, some text is black (likely `text-muted` which ignores custom CSS variables).
  **Fix:** Replace `text-muted` with `text-muted-custom` throughout `public_profile.html`.

- [ ] **G-MED-2 · Recipe privacy (`is_public`) not surfaced in create/edit form**
  `Recipe.is_public` exists and defaults to `True`, but there is no toggle in the create/edit form. Users cannot create private/unlisted recipes.
  **Fix:** Add a "Private" checkbox to `create.html`/`RecipeForm`; honour it in `discover` and `/api/recipes` queries.

- [ ] **G-MED-3 · Follow/Unfollow button missing on Home and Discover pages**
  Creator names appear on recipe cards across Home and Discover but have no inline Follow button. Users must navigate to Community or a profile page to follow.
  **Fix:** Add a small `<button class="follow-btn">` next to creator links in `_recipe_card.html`, reusing the `fetch` POST pattern from `feed.html`.

- [ ] **G-MED-4 · Footer background doesn't update with dark/light theme toggle**
  In light mode the footer keeps the wrong background colour instead of matching the light surface.
  **Fix:** Ensure `footer` in `style.css` uses `background: var(--pt-bg)` and the `[data-theme="light"]` block overrides it correctly.

- [ ] **G-MED-5 · Browser back-button causes theme flash then incorrect state**
  Steps: toggle dark mode → navigate → press back → page loads light → click any link → page is dark again without touching toggle. Back-forward cache restores the page without re-running the inline theme script.
  **Fix:** Add a `pageshow` listener in `base.html` that re-applies the stored theme: `window.addEventListener('pageshow', applyTheme)`.

- [ ] **G-MED-6 · Symbol-only recipe title produces a 404 slug**
  A title of `!!!` generates an empty or whitespace-only slug. The record is saved but any URL navigation → 404. Subsequent symbol-only recipes get slugs `-1`, `-2`, etc.
  **Fix:** In `Recipe.generate_slug`, if the slugified result is empty or only hyphens, fall back to `recipe-<id>` or a UUID fragment.

- [ ] **G-MED-7 · Deprecated SQLAlchemy API: `MealPlanItem.query.get()`**
  `planner/routes.py:122` — deprecated in SQLAlchemy 2.x.
  **Fix:** `db.session.get(MealPlanItem, int(item_id))`.

- [ ] **G-MED-8 · Hardcoded `redirect('/')` in auth routes**
  `auth/routes.py:23, 41, 50` use literal `redirect('/')` instead of `redirect(url_for('recipes.home'))`. URL changes would silently break redirects.
  **Fix:** Use `url_for` consistently.

- [ ] **G-MED-9 · `User.email` selected in leaderboard query but never rendered**
  `community/routes.py:49` includes `User.email` in the leaderboard `group_by`. Never displayed, but accidental rendering would leak emails publicly.
  **Fix:** Remove `User.email` from the query.

- [ ] **X-MED-2 · Pantry AI write-then-call has no transaction safety**
  `ai/routes.py` DELETE pantry → INSERT new items → OpenAI call → `commit()`. If the network call hangs after DELETE+INSERT but before commit, the user's pantry is silently wiped.
  **Fix:** Commit pantry changes in a separate `db.session.commit()` block before the AI call.

- [ ] **X-MED-3 · Bare `except Exception` in AI service swallows all errors**
  `ai/services.py:79-80`: `except Exception: return []` — rate-limit errors, key revocations, and programming bugs all return empty with no log.
  **Fix:** `except Exception as e: current_app.logger.exception('ai_suggest failed'); return []`

- [ ] **X-MED-4 · OpenAI prompt is vulnerable to prompt injection**
  User-controlled `ingredients` and `preferences` interpolated directly into system prompt. A malicious `preferences` value can subvert the JSON shape or leak prompt content.
  **Fix:** Wrap user content in delimiters in the prompt and instruct the model to treat it as data only.

- [ ] **X-MED-5 · `get_pantry_matches` is N+1**
  `ai/services.py:20-31` — issues a fresh `RecipeIngredient.query.filter_by(recipe_id=...)` per recipe. 50 recipes = 51 DB queries.
  **Fix:** Use `selectinload(Recipe.ingredients)` or a single join+aggregate query.

- [ ] **X-MED-6 · Profile tab URL hash injected unsafely into CSS selector**
  `profile.html` — `document.querySelector(\`[data-bs-target="${hash}"]\`)` with unvalidated hash. A hash like `#"]; alert(1) //` throws `SyntaxError` and breaks all JS on the page.
  **Fix:** Validate `hash.match(/^#[a-z\-]{1,32}$/i)` before using.

- [ ] **X-MED-8 · `_get_or_create_plan` writes to DB on a GET request**
  First visit to `/planner` silently inserts a `MealPlan` row — state-changing GET.
  **Fix:** Create the row lazily on the first `POST /api/planner/save` instead.

- [ ] **X-MED-9 · Planner and grocery list render soft-deleted recipes**
  `MealPlanItem.recipe` joins `recipe.id` without filtering `is_deleted=False`. Deleted recipes still appear in users' planners.
  **Fix:** Add `is_deleted=False` to the join or show "(deleted)" as a placeholder.

---

### H-LOW — Low: Code Quality & Polish

- [ ] **X-LOW-5 · `{{ total }}` interpolated as bare JS literal**
  `discover.html:76`: `let totalResults = {{ total }};` — if `total` is ever `None`, produces invalid JS. Use `{{ total|tojson }}`.

- [ ] **X-LOW-8 · Follow toggle logic duplicated between `feed.html` and `public_profile.html`**
  Extract a shared `toggleFollow(username, btn)` helper into `main.js`.

- [ ] **X-LOW-9 · Recipe slug not JSON-encoded in `detail.html`**
  `const slug = '{{ recipe.slug }}';` — use `const slug = {{ recipe.slug|tojson }};` for safety.

- [ ] **X-LOW-10 · `MealPlan.user_id` and `MealPlanItem.mealplan_id` not `nullable=False`**
  `models.py:128, 142` — allows orphaned rows at ORM level. Add `nullable=False` and `ondelete='CASCADE'`.

- [ ] **X-LOW-12 · `request.get_json(silent=True) or {}` repeated in 6 routes**
  Extract a `_json_body()` helper so all routes handle missing/malformed bodies identically and log the fallback.

- [ ] **X-LOW-13 · No `413` error handler for oversized uploads**
  `config.py` sets `MAX_CONTENT_LENGTH = 4 MB` but an oversized upload returns Werkzeug's generic 413 page.
  **Fix:** Add `@app.errorhandler(413)` flashing "File too large (max 4 MB)" and redirecting back.

- [ ] **X-LOW-15 · `Recipe.generate_slug` is O(n) per insert**
  Each retry hits the DB individually. Use a single `slug LIKE base%` query to find the highest suffix in Python.

- [ ] **X-LOW-16 · No HTTP security headers**
  `app/__init__.py` sets no `Content-Security-Policy`, `X-Content-Type-Options`, or `X-Frame-Options`. A strict CSP would also mitigate X-CRIT-2.

- [ ] **G-LOW-1 · Footer year still hard-coded**
  Currently correct at "2026" but will break in January 2027. Use a context processor:
  ```python
  @app.context_processor
  def inject_year():
      return {'current_year': datetime.utcnow().year}
  ```
  Then in `base.html`: `© {{ current_year }}`.

---

### H-XREF — Already in AUDIT.md (no action needed, listed for traceability)

| Group doc item | AUDIT.md entry |
|---|---|
| Deleted recipes show on My Meals | D11 |
| Orphaned `static/style.css` | D13 |
| "New This Week" no date filter | C5 |
| Follow returns 405 (Method Not Allowed) | A1 |
| "Add to Meal Plan" → `/planner` | B2 / C-V9 |
| Comment author not linked to profile | C-V19 |
| Profile picture can't be changed | C15 / U20 |
| Grocery checkbox IDs from raw ingredient names | D8 |
| `planner_save` 500 on bad `recipe_id` | D15 |
| Open redirect on `/login` | C12 |
| Double reload after planner save | D9 |
| Category badge not linked | C4 |
| XSS risk in `pantry.js` / discover (code-quality note) | D14 / A5 |
