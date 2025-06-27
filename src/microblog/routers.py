import os
from typing import Optional, List
import secrets

from sqlalchemy.orm import Session
from pydantic import BaseModel

from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import APIRouter, HTTPException, Cookie, Response, Depends, Form

from passlib.hash import bcrypt

from .database import SessionLocal
from .models import User, MicroblogPost
from .templates.utils import format_datetime

template_path = os.path.join(
    os.path.dirname(__file__), 'templates'
)
templates = Jinja2Templates(directory=template_path)
templates.env.filters["format_datetime"] = format_datetime

auth = APIRouter()
posts = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

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

SECRET_KEY = os.environ["SESSION_SECRET_KEY"]

def create_session_token(user_id: int) -> str:
    # Simple example: sign user_id with SECRET_KEY, use itsdangerous or JWT
    from itsdangerous import URLSafeSerializer
    s = URLSafeSerializer(SECRET_KEY)
    return s.dumps({"user_id": user_id})

def verify_session_token(token: str) -> int:
    from itsdangerous import URLSafeSerializer, BadSignature
    s = URLSafeSerializer(SECRET_KEY)
    try:
        data = s.loads(token)
        return data["user_id"]
    except BadSignature:
        raise HTTPException(status_code=401, detail="Invalid session")

def get_current_user_id(session_token: Optional[str] = Cookie(None)) -> int:
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return verify_session_token(session_token)

def get_current_user_id_optional(session_token: Optional[str] = Cookie(None)) -> Optional[int]:
    if not session_token:
        return None
    try:
        return verify_session_token(session_token)
    except HTTPException:
        return None


@auth.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@auth.post("/login")
def login(
    request: Request,
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.username == username).first()
    if not user or not bcrypt.verify(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_session_token(user.id)

    redirect_response = RedirectResponse(
        url="/posts", status_code=303
    )
    redirect_response.set_cookie(
        key="session_token", value=token, httponly=True, secure=False
    )

    return redirect_response

@auth.post("/logout")
def logout():
    response = RedirectResponse(url="/posts", status_code=303)
    response.delete_cookie("session_token")
    return response


@posts.get("/", response_class=HTMLResponse)
def view_all_posts(
    request: Request,
    user_id: Optional[int] = Depends(get_current_user_id_optional),
    db: Session = Depends(get_db)
):
    all_posts = (
        db.query(MicroblogPost)
        .order_by(MicroblogPost.created_at.desc())
        .all()
    )
    return templates.TemplateResponse(
        "posts.html", {"request": request, "posts": all_posts, "user_logged_in": user_id is not None}
    )

@posts.get("/create", response_class=HTMLResponse)
def create_post_form(request: Request, author_id: int = Depends(get_current_user_id)):
    return templates.TemplateResponse("create_post.html", {"request": request})


@posts.post("/create")
def create_post_via_form(
    request: Request,
    author_id: int = Depends(get_current_user_id),
    content: str = Form(...),
    in_reply_to_post_id: Optional[str] = Form(None),
    in_reply_to_user_id: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
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


# Post creation
@posts.post("/", response_model=MicroblogOut)
def create_post(post: MicroblogCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == post.author_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    new_post = MicroblogPost(
        author_id=post.author_id,
        content=post.content,
        in_reply_to_post_id=post.in_reply_to_post_id,
        in_reply_to_user_id=post.in_reply_to_user_id,
    )
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return new_post

# Get all posts for a specific user
@posts.get("/user/{user_id}", response_model=List[MicroblogOut])
def get_user_posts(user_id: int, db: Session = Depends(get_db)):
    posts = (
        db.query(MicroblogPost)
        .filter(MicroblogPost.author_id == user_id)
        .order_by(MicroblogPost.created_at.desc())
        .all()
    )
    return posts
