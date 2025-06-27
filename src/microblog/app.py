# FastAPI application for a microblogging service
import os
from fastapi import FastAPI
from sqlalchemy.orm import Session
from passlib.hash import bcrypt

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request
from .routers import auth, posts, templates

from .database import SessionLocal
from .models import User

app = FastAPI()

@app.on_event("startup")
def create_admin_user():
    db: Session = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == "admin").first()
        if not existing:
            password = os.getenv("MICROBLOG_ADMIN_PASSWORD")
            if not password:
                raise RuntimeError("MICROBLOG_ADMIN_PASSWORD is not set")
            hashed = bcrypt.hash(password)
            admin = User(
                username="admin",
                email="admin@example.com",
                hashed_password=hashed
            )
            db.add(admin)
            db.commit()
    finally:
        db.close()


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return RedirectResponse('/posts')

# Include routers
app.include_router(auth, prefix="/auth", tags=["auth"])
app.include_router(posts, prefix="/posts", tags=["posts"])
