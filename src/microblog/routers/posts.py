from typing import Optional

from sqlalchemy.orm import Session
from pydantic import BaseModel

from fastapi.requests import Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import APIRouter, HTTPException, Depends, Form

from .auth import get_current_user_id, get_current_user_id_optional

from ..database import get_db
from ..models import User, MicroblogPost
from ..template_utils import templates

posts = APIRouter()

# Schemas
class MicroblogCreate(BaseModel):
    author_id: int
    content: str
    in_reply_to_post_id: Optional[int] = None
    in_reply_to_user_id: Optional[int] = None

class MicroblogOut(BaseModel):
    id: int
    author_id: int
    content: str
    created_at: str
    in_reply_to_post_id: Optional[int]
    in_reply_to_user_id: Optional[int]

    class Config:
        from_attributes = True


@posts.get("/", response_class=HTMLResponse)
def view_all_posts(
    request: Request,
    user_id: Optional[int] = Depends(get_current_user_id_optional),
    db: Session = Depends(get_db)
):
    """Render page with all posts"""
    all_posts = (
        db.query(MicroblogPost)
        .order_by(MicroblogPost.created_at.desc())
        .all()
    )
    return templates.TemplateResponse(
        "posts.html",
        {
            "request": request,
            "posts": all_posts,
            "user_logged_in": user_id is not None
        }
    )

@posts.get("/create", response_class=HTMLResponse)
def create_post_form(
    request: Request, author_id: int = Depends(get_current_user_id)
):
    """Render page with form to create new post"""
    return templates.TemplateResponse(
        "create_post.html", {"request": request}
    )


@posts.post("/create")
def create_post_via_form(
    request: Request,
    author_id: int = Depends(get_current_user_id),
    content: str = Form(...),
    in_reply_to_post_id: Optional[str] = Form(None),
    in_reply_to_user_id: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """Create posts from submitted form"""
    user = db.query(User).filter(User.id == author_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Convert empty strings to None, otherwise cast to int
    post_id = int(in_reply_to_post_id) if in_reply_to_post_id else None
    user_id = int(in_reply_to_user_id) if in_reply_to_user_id else None

    new_post = MicroblogPost(
        author_id=author_id,
        content=content,
        in_reply_to_post_id=post_id,
        in_reply_to_user_id=user_id,
    )
    db.add(new_post)
    db.commit()
    return RedirectResponse(url="/posts", status_code=303)
