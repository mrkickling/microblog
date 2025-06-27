# models.py
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(32), unique=True, nullable=False)
    email = Column(String(128), unique=True, nullable=False)
    hashed_password = Column(String(256), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    posts = relationship(
        "MicroblogPost",
        back_populates="author",
        foreign_keys="MicroblogPost.author_id"
    )


class MicroblogPost(Base):
    __tablename__ = "microblog_posts"

    id = Column(Integer, primary_key=True)
    author_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Reply to another post or user
    in_reply_to_post_id = Column(Integer, ForeignKey("microblog_posts.id", ondelete="SET NULL"), nullable=True)
    in_reply_to_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    author = relationship("User", back_populates="posts", foreign_keys=[author_id])
    replies = relationship("MicroblogPost", backref="parent_post", remote_side=[id])
