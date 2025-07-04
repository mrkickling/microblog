from typing import Optional

from sqlalchemy.orm import Session

from fastapi.requests import Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import APIRouter, HTTPException, Depends

from .auth import get_current_user_id_optional

from ..database import get_db
from ..models import User, MicroblogPost
from ..template_utils import templates

users = APIRouter()

@users.get("/", response_class=HTMLResponse)
def view_all_users(
    request: Request,
):
    """Render page with all posts"""
    return RedirectResponse('/posts')


@users.get("/{username}", response_class=HTMLResponse)
def view_users_posts(
    request: Request,
    username: str,
    user_id: Optional[int] = Depends(get_current_user_id_optional),
    db: Session = Depends(get_db)
):
    """Render page with a specific users posts"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    all_posts = (
        db.query(MicroblogPost)
        .order_by(MicroblogPost.created_at.desc())
        .filter(MicroblogPost.author_id == user.id)
        .all()
    )
    return templates.TemplateResponse(
        "posts.html",
        {
            "by_user": user,
            "request": request,
            "posts": all_posts,
            "user_logged_in": user_id
        }
    )
