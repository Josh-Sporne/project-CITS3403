from flask import Blueprint

bp = Blueprint('planner', __name__)

from app.planner import routes  # noqa: E402, F401
