# Plate Theory

A community-driven meal planning web app where users discover recipes, plan weekly meals, generate grocery lists, and get smart meal suggestions based on pantry ingredients.

## Purpose

Plate Theory solves the daily problem of "what should I eat?" by combining recipe sharing, weekly meal planning, and smart grocery list generation into one platform. Users can:

- **Create and share recipes** with the community
- **Discover recipes** through search, category filters, and trending feeds
- **Plan weekly meals** on an interactive calendar with breakfast/lunch/dinner slots
- **Auto-generate grocery lists** from meal plans, minus what's already in their pantry
- **Get ingredient-matched suggestions** based on what they have on hand
- **Engage socially** — rate, comment, follow cooks, and compete on leaderboards

## Team

| UWA ID | Name   | GitHub Username |
|--------|--------|-----------------|
| ...    | Rania  | raniak25        |
| ...    | Josh   | Josh-Sporne     |
| ...    | Yifeng | Yifeng-593      |
| ...    | Olivia | OliviaSynn      |

## Architecture

- **Backend:** Python 3 / Flask with Blueprints (auth, recipes, planner, ai, community)
- **Database:** SQLite via SQLAlchemy ORM with Flask-Migrate for schema migrations
- **Frontend:** Bootstrap 5 with custom CSS (dark/light theme toggle), vanilla JavaScript (ES6+)
- **Authentication:** Flask-Login with session-based auth and Werkzeug password hashing
- **Forms & Security:** Flask-WTF with CSRF protection on all forms and AJAX requests
- **Pantry Matching:** Database-driven ingredient matching with optional OpenAI integration

### Database Schema

10 models with relationships, indexes, and unique constraints:

| Model | Purpose |
|-------|---------|
| User | Accounts with hashed passwords, bios, Gravatar avatars |
| Recipe | Titles, slugs, descriptions, instructions, categories, soft deletes |
| RecipeIngredient | Ingredient names, quantities, and units per recipe |
| MealPlan | Weekly plans tied to a user and a week-start date |
| MealPlanItem | Individual meal slots (day + meal type) linking to recipes or custom text |
| Rating | 1–5 star ratings with unique constraint per user/recipe pair |
| Comment | Timestamped comments on recipes |
| SavedRecipe | Bookmark/save toggle per user/recipe pair |
| PantryItem | User's pantry ingredients for matching |
| Follower | Follower/followed relationships between users |

### Key Routes

| Feature | Route | Description |
|---------|-------|-------------|
| Home | `/` | Trending recipes, new this week, quick actions |
| Discover | `/discover` | Search, filter by category, sort, AJAX pagination |
| Recipe Detail | `/recipe/<slug>` | Ingredients, instructions, star ratings, comments |
| Create/Edit Recipe | `/recipe/create` | Form with dynamic ingredient rows, image upload |
| Meal Planner | `/planner` | Weekly grid, click-to-assign modal, day/week toggle |
| Grocery List | `/grocery` | Auto-generated from meal plan, pantry exclusion |
| Pantry Suggestions | `/pantry` | Ingredient input, DB matching with percentage scores |
| Community | `/community` | Feed from followed users, monthly leaderboard |
| Profile | `/profile` | Dashboard with recipes, saved items, stats, bio editor |
| Public Profile | `/user/<username>` | View another user's recipes and follow/unfollow |

### Project Structure

```
project-CITS3403-1/
├── app/
│   ├── __init__.py              # App factory, extensions, blueprint registration
│   ├── models.py                # All 10 SQLAlchemy models
│   ├── auth/                    # Registration, login, logout, profile routes & forms
│   ├── recipes/                 # Recipe CRUD, ratings, comments, save/unsave, discover
│   ├── planner/                 # Meal planner grid, AJAX save/remove, grocery list API
│   ├── ai/                      # Pantry ingredient matching, OpenAI suggestions
│   ├── community/               # Feed, leaderboard, follow/unfollow
│   ├── static/
│   │   ├── css/style.css        # Full dark/light theme with CSS variables
│   │   ├── js/                  # main.js, discover.js, planner.js, pantry.js, validation.js
│   │   └── uploads/             # User-uploaded recipe images
│   └── templates/               # Jinja2 templates organised by blueprint
├── migrations/                  # Alembic migration scripts
├── tests/
│   ├── unit/                    # 10 unit tests (auth, recipes, ratings, planner)
│   └── selenium/                # 6 browser tests (registration, login, page flows)
├── config.py                    # Config and TestConfig classes
├── run.py                       # Application entry point
├── seed.py                      # Demo data seeder
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variable template
└── .gitignore
```

## Setup and Launch

### macOS / Linux

```bash
# Clone the repository (from the feature-rania branch)
git clone -b feature-rania https://github.com/Josh-Sporne/project-CITS3403.git
cd project-CITS3403

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your own SECRET_KEY (and OPENAI_API_KEY if using AI features)

# Initialize database
flask db upgrade

# Load demo data (optional)
python seed.py

# Run the application
flask run
```

### Windows

```cmd
:: Clone the repository (from the feature-rania branch)
git clone -b feature-rania https://github.com/Josh-Sporne/project-CITS3403.git
cd project-CITS3403

:: Create virtual environment
python -m venv .venv
.venv\Scripts\activate

:: Install dependencies
pip install -r requirements.txt

:: Configure environment
copy .env.example .env
:: Edit .env with your own SECRET_KEY (and OPENAI_API_KEY if using AI features)

:: Initialize database
flask db upgrade

:: Load demo data (optional)
python seed.py

:: Run the application
flask run
```

Open [http://localhost:5000](http://localhost:5000) in your browser.

**Demo login:** username `rania`, password `password123`

## Working on Your Own Branch

After cloning, switch to your own branch so changes don't affect `feature-rania`:

### If creating a new branch

```bash
# Replace "feature-yourname" with your actual branch name
git checkout -b feature-yourname
git push -u origin feature-yourname
```

### If you already have a branch on remote

```bash
git checkout feature-yourname
git merge origin/feature-rania
git push
```

## Running Tests

### Unit Tests

```bash
python -m pytest tests/unit/ -v
```

10 unit tests covering:
- User registration, login, and password hashing
- Protected route access control (redirect when not logged in)
- Recipe CRUD with automatic slug generation
- Ownership verification (403 on unauthorized edit/delete)
- Rating average computation and upsert behaviour
- Grocery list ingredient aggregation from meal plans
- Pantry item exclusion from grocery lists

### Selenium Tests

Requires Chrome and ChromeDriver installed.

```bash
# Start the application in one terminal
flask run

# Run Selenium tests in another terminal
python -m pytest tests/selenium/ -v
```

6 Selenium tests covering:
- User registration flow
- Login flow
- Recipe viewing
- Discover page loading
- Recipe creation
- Community page access

## Security

- **Password storage:** Salted hashes via Werkzeug (`generate_password_hash` / `check_password_hash`), never stored in plaintext
- **CSRF protection:** Flask-WTF `CSRFProtect` enabled globally; tokens embedded in all forms via `{{ form.hidden_tag() }}` and sent as `X-CSRFToken` headers on AJAX requests
- **Environment variables:** Secret key, database URL, and API keys stored in `.env` (gitignored), with `.env.example` as a template
- **Authorization:** `@login_required` on all protected routes; owner-only checks on recipe edit/delete (returns 403)
- **Rate limiting:** AI suggestion endpoint limited to one request per 30 seconds per user

## Technologies

| Technology | Purpose |
|------------|---------|
| Python 3 | Backend language |
| Flask | Web framework |
| SQLAlchemy | ORM and database abstraction |
| SQLite | Database engine |
| Flask-Login | Session-based authentication |
| Flask-WTF | Form handling and CSRF protection |
| Flask-Migrate | Database schema migrations (Alembic) |
| Bootstrap 5 | Responsive CSS framework |
| Bootstrap Icons | Icon library |
| JavaScript (ES6+) | Client-side interactivity and AJAX |
| OpenAI API | Meal suggestions (optional) |
| Selenium | Browser automation testing |
| pytest | Test runner |
