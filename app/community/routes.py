from datetime import datetime, timezone

from flask import render_template, jsonify
from flask_login import login_required, current_user

from app import db
from app.models import Recipe, User, Follower
from app.community import bp

from sqlalchemy import func


@bp.route('/community')
def feed():
    recipes_query = Recipe.query.filter_by(
        is_public=True, is_deleted=False
    ).order_by(Recipe.created_at.desc())

    followed_recipes = []
    if current_user.is_authenticated:
        followed_ids = [
            f.followed_id for f in
            Follower.query.filter_by(follower_id=current_user.id).all()
        ]
        if followed_ids:
            followed_recipes = Recipe.query.filter(
                Recipe.creator_id.in_(followed_ids),
                Recipe.is_public == True,   # noqa: E712
                Recipe.is_deleted == False,  # noqa: E712
            ).order_by(Recipe.created_at.desc()).limit(20).all()

    recent_recipes = recipes_query.limit(20).all()

    if followed_recipes:
        seen = {r.id for r in followed_recipes}
        combined = list(followed_recipes)
        for r in recent_recipes:
            if r.id not in seen:
                combined.append(r)
                seen.add(r.id)
        recent_recipes = combined[:30]

    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    leaderboard = (
        db.session.query(
            User.username,
            User.email,
            func.count(Recipe.id).label('recipe_count')
        )
        .join(Recipe, Recipe.creator_id == User.id)
        .filter(
            Recipe.is_public == True,   # noqa: E712
            Recipe.is_deleted == False,  # noqa: E712
            Recipe.created_at >= month_start,
        )
        .group_by(User.id, User.username, User.email)
        .order_by(func.count(Recipe.id).desc())
        .limit(10)
        .all()
    )

    return render_template(
        'community/feed.html',
        recipes=recent_recipes,
        leaderboard=leaderboard,
    )


@bp.route('/user/<username>/follow', methods=['POST'])
@login_required
def toggle_follow(username):
    target = User.query.filter_by(username=username).first_or_404()
    if target.id == current_user.id:
        return jsonify(success=False, error='Cannot follow yourself'), 400

    existing = Follower.query.filter_by(
        follower_id=current_user.id, followed_id=target.id
    ).first()

    if existing:
        db.session.delete(existing)
        following = False
    else:
        db.session.add(Follower(
            follower_id=current_user.id,
            followed_id=target.id,
        ))
        following = True

    db.session.commit()

    follower_count = Follower.query.filter_by(followed_id=target.id).count()

    return jsonify(
        success=True,
        following=following,
        follower_count=follower_count,
    )
