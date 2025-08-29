# models.py
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, select, func
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

# PostLike must be defined first

class PostLike(Base):
    __tablename__ = "microblog_likes"

    id = Column(Integer, primary_key=True)
    time = Column(DateTime(timezone=True), server_default=func.now())
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    post_id = Column(Integer, ForeignKey("microblog_posts.id", ondelete="CASCADE"), nullable=False)

    liked_by = relationship("User", back_populates="likes", foreign_keys=[user_id])
    post = relationship("MicroblogPost", back_populates="likes", foreign_keys=[post_id])


class MicroblogPost(Base):
    __tablename__ = "microblog_posts"

    id = Column(Integer, primary_key=True)
    author_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    in_reply_to_post_id = Column(Integer, ForeignKey("microblog_posts.id", ondelete="SET NULL"), nullable=True)
    in_reply_to_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    author = relationship("User", back_populates="posts", foreign_keys=[author_id])
    replies = relationship(
        "MicroblogPost",
        back_populates="reply_to",
        cascade="all, delete-orphan",
        passive_deletes=True,
        foreign_keys=[in_reply_to_post_id]
    )
    reply_to = relationship(
        "MicroblogPost",
        remote_side=[id],
        primaryjoin="MicroblogPost.in_reply_to_post_id==MicroblogPost.id",
        uselist=False
    )
    likes = relationship(
        "PostLike",
        back_populates="post",
        foreign_keys=[PostLike.post_id],
        cascade="all, delete-orphan"
    )
    # many-to-many Post <-> User through PostLike
    liked_by = relationship(
        "User",
        secondary="microblog_likes",
        back_populates="liked_posts",
        viewonly=True
    )

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
        foreign_keys=[MicroblogPost.author_id]
    )

    likes = relationship(
        "PostLike",
        back_populates="liked_by",
        foreign_keys=[PostLike.user_id],
        cascade="all, delete-orphan"
    )
    # many-to-many User <-> Post through PostLike
    liked_posts = relationship(
        "MicroblogPost",
        secondary="microblog_likes",
        back_populates="liked_by",
        viewonly=True
    )
