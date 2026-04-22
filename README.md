# Plate Theory

A community-driven meal planning web app where users discover recipes, plan weekly meals, generate grocery lists, and get AI-powered meal suggestions based on pantry ingredients.

## Purpose

Plate Theory solves the daily problem of "what should I eat?" by combining recipe sharing, weekly meal planning, and smart grocery list generation into one platform. Users can:

- **Create and share recipes** with the community
- **Discover recipes** through search, category filters, and trending feeds
- **Plan weekly meals** on an interactive calendar with breakfast/lunch/dinner slots
- **Auto-generate grocery lists** from meal plans, minus what's already in their pantry
- **Get AI-powered suggestions** based on ingredients they have on hand
- **Engage socially** — rate, comment, follow cooks, and compete on leaderboards

## Team

| UWA ID | Name   | GitHub Username |
|--------|--------|-----------------|
| ...    | Rania  | raniak25        |
| ...    | Josh   | Josh-Sporne     |
| ...    | Yifeng | ...             |
| ...    | Olivia | ...             |

## Architecture

- **Backend:** Flask with Blueprints (auth, recipes, planner, ai, community)
- **Database:** SQLite via SQLAlchemy with Flask-Migrate for migrations
- **Frontend:** Bootstrap 5 dark theme, vanilla JavaScript, jQuery
- **Authentication:** Flask-Login with session management and password hashing
- **AI:** Optional OpenAI integration for meal suggestions + database-driven pantry matching

### Database Schema

10 tables: User, Recipe, RecipeIngredient, MealPlan, MealPlanItem, Rating, Comment, SavedRecipe, PantryItem, Follower

### Key Features

| Feature | Route | Description |
|---------|-------|-------------|
| Home | `/` | Trending recipes, new this week, quick actions |
| Discover | `/discover` | Search, filter by category, sort, AJAX pagination |
| Recipe Detail | `/recipe/<slug>` | Ingredients, instructions, ratings, comments |
| Create Recipe | `/recipe/create` | Form with dynamic ingredients, image upload |
| Meal Planner | `/planner` | Weekly calendar, click-to-assign, day/week toggle |
| Grocery List | `/grocery` | Auto-generated checklist, pantry exclusion, export |
| Pantry AI | `/pantry` | Ingredient input, DB matching, optional AI suggestions |
| Community | `/community` | Feed from followed users, leaderboard |
| Profile | `/profile` | Dashboard with recipes, saves, stats, settings |

## Setup and Launch

```bash
# Clone the repository
git clone https://github.com/Josh-Sporne/project-CITS3403.git
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

Open [http://localhost:5000](http://localhost:5000) in your browser.

**Demo login credentials:** username `rania`, password `password123`

## Running Tests

### Unit Tests

```bash
python -m pytest tests/unit/ -v
```

10 unit tests covering:
- User registration and authentication
- Protected route access control
- Recipe CRUD with slug generation
- Ownership verification (403 on unauthorized edit)
- Rating average computation and upsert behavior
- Grocery list ingredient aggregation
- Pantry item exclusion from grocery lists

### Selenium Tests

Requires Chrome and ChromeDriver installed.

```bash
# Start the application in one terminal
flask run

# Run selenium tests in another terminal
python -m pytest tests/selenium/ -v
```

6 Selenium tests covering:
- User registration flow
- Login flow
- Recipe viewing
- Discover page loading
- Recipe creation
- Community page access

## Technologies

| Technology | Purpose |
|------------|---------|
| Flask | Web framework |
| SQLAlchemy | ORM / database |
| SQLite | Database engine |
| Flask-Login | Session management |
| Flask-WTF | Form handling + CSRF |
| Flask-Migrate | Database migrations |
| Bootstrap 5 | CSS framework |
| Bootstrap Icons | Icon library |
| JavaScript (ES6+) | Client-side interactivity |
| OpenAI API | AI meal suggestions (optional) |
| Selenium | Browser testing |
