# FastAPI application for a microblogging service
import os
from sqlalchemy.orm import Session
from passlib.hash import bcrypt

from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import FastAPI, Request

from .database import SessionLocal
from .models import User
from .routers import auth, posts

app = FastAPI()

@app.on_event("startup")
def create_admin_user():
    db: Session = SessionLocal()
    username = os.getenv("MICROBLOG_ADMIN_USERNAME", "admin")
    try:
        existing = db.query(User).filter(User.username == username).first()
        if not existing:
            password = os.getenv("MICROBLOG_ADMIN_PASSWORD", "password")

            hashed = bcrypt.hash(password)
            admin = User(
                username=username,
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
