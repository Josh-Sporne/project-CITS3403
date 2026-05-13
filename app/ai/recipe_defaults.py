"""Defaults and limits for persisting AI-generated recipes as Recipe rows."""

DEFAULT_AI_CATEGORY = 'dinner'
DEFAULT_AI_COOKING_TIME = 30
MAX_INSTRUCTIONS_LEN = 20000
MAX_INGREDIENT_ROWS = 40
MAX_INGREDIENT_NAME_LEN = 100

# Max AI saves per user per hour (abuse guard)
MAX_AI_SAVES_PER_HOUR = 10
