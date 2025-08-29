import os
from typing import Optional

from sqlalchemy.orm import Session

from fastapi.requests import Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import APIRouter, HTTPException, Cookie, Response, Depends, Form
from passlib.hash import bcrypt

from ..database import get_db
from ..models import User
from ..template_utils import templates

auth = APIRouter()

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
    """Render login form page"""
    return templates.TemplateResponse("login.html", {"request": request})


@auth.post("/login")
def login(
    request: Request,
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    """If correct credentials, create token and store in session cookie"""
    user = db.query(User).filter(User.username == username).first()
    if not user or not bcrypt.verify(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_session_token(user.id)

    redirect_response = RedirectResponse(
        url="/posts", status_code=303
    )
    redirect_response.set_cookie(
        key="session_token",
        value=token,
        httponly=True,
        secure=False,
        max_age=60 * 60 * 24 * 30,   # 30 days in seconds
        expires=60 * 60 * 24 * 30    # some clients require explicit expires
    )

    return redirect_response


@auth.get("/register", response_class=HTMLResponse)
def register_form(request: Request):
    """Render login form page"""
    return templates.TemplateResponse("register.html", {"request": request})


@auth.post("/register")
def register(
    request: Request,
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
    email: str = Form(...),
    db: Session = Depends(get_db),
):
    """If correct credentials, create token and store in session cookie"""
    user = db.query(User).filter(User.username == username).first()
    if user:
        raise HTTPException(status_code=400, detail="Username already taken")

    new_user = User(
        username=username,
        email=email,
        hashed_password=bcrypt.hash(password)
    )

    db.add(new_user)
    db.commit()

    return RedirectResponse(
        url="/auth/login", status_code=303
    )

@auth.post("/logout")
def logout():
    """Log user out (remove cookie)"""
    response = RedirectResponse(url="/posts", status_code=303)
    response.delete_cookie("session_token")
    return response
