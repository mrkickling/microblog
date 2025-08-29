from typing import Optional

from sqlalchemy.orm import Session, selectinload
from pydantic import BaseModel

from fastapi.requests import Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import APIRouter, HTTPException, Depends, Form

from .auth import get_current_user_id, get_current_user_id_optional

from ..database import get_db
from ..models import User, MicroblogPost, PostLike
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
        .filter(MicroblogPost.in_reply_to_post_id == None)
        .options(selectinload(MicroblogPost.likes))
        .order_by(MicroblogPost.created_at.desc())
        .all()
    )
    return templates.TemplateResponse(
        "posts.html",
        {
            "request": request,
            "posts": all_posts,
            "user_id_logged_in": user_id,
            "user_logged_in": db.query(User).get(user_id) if user_id else None
        }
    )


@posts.get("/{post_id}", response_class=HTMLResponse)
def view_single_posts(
    request: Request,
    post_id: int,
    user_id: Optional[int] = Depends(get_current_user_id_optional),
    db: Session = Depends(get_db)
):
    """Render page with single post"""
    post = db.query(MicroblogPost).filter_by(id=post_id).first()
    return templates.TemplateResponse(
        "post.html",
        {
            "request": request,
            "post": post,
            "user_id_logged_in": user_id,
            "user_logged_in": db.query(User).get(user_id) if user_id else None
        }
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
    return RedirectResponse(url=f"/posts/{new_post.id}", status_code=303)


@posts.post("/delete")
def delete_post_via_form(
    request: Request,
    author_id: int = Depends(get_current_user_id),
    post_id: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """Delete posts from submitted form"""
    user = db.query(User).filter(User.id == author_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    post = db.query(MicroblogPost).filter(
        MicroblogPost.id == post_id,
        MicroblogPost.author_id == author_id
    ).first()

    if post:
        db.delete(post)
        db.commit()

    return RedirectResponse(url="/posts", status_code=303)


@posts.post("/like")
def like_post_via_form(
    request: Request,
    liked_by: int = Depends(get_current_user_id),
    post_id: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """Create like from submitted form"""
    user = db.query(User).filter(User.id == liked_by).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    post = db.query(MicroblogPost).filter(
        MicroblogPost.id == post_id
    ).first()

    like = db.query(PostLike).filter(
        PostLike.post_id == post_id,
        PostLike.user_id == liked_by
    ).first()

    if post and not like:
        # Create like if post exists but like does not
        like = PostLike(
            post_id=post_id,
            user_id=liked_by
        )
        db.add(like)
        db.commit()
    elif post and like:
        db.delete(like)
        db.commit()

    return RedirectResponse(url="/posts", status_code=303)
