from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, Boolean, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    avatar = Column(String(255), default="default_avatar.png")
    bio = Column(Text, default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    corners = relationship("Corner", back_populates="author")
    checkins = relationship("CheckIn", back_populates="user")
    routes = relationship("Route", back_populates="user")
    achievements = relationship("UserAchievement", back_populates="user")
    shares = relationship("Share", back_populates="user")
    images = relationship("Image", back_populates="user")


class Corner(Base):
    __tablename__ = "corners"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(50), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    address = Column(String(255))
    images = Column(String(255), default="")
    tags = Column(String(255), default="")
    difficulty = Column(String(20), default="easy")
    is_hidden = Column(Boolean, default=False)
    author_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    author = relationship("User", back_populates="corners")
    checkins = relationship("CheckIn", back_populates="corner")
    route_corners = relationship("RouteCorner", back_populates="corner")


class CheckIn(Base):
    __tablename__ = "checkins"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    corner_id = Column(Integer, ForeignKey("corners.id"))
    content = Column(Text, default="")
    images = Column(String(255), default="")
    rating = Column(Integer, default=5)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="checkins")
    corner = relationship("Corner", back_populates="checkins")


class Route(Base):
    __tablename__ = "routes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String(100), nullable=False)
    description = Column(Text, default="")
    estimated_time = Column(Integer, default=60)
    distance = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="routes")
    corners = relationship("RouteCorner", back_populates="route")


class RouteCorner(Base):
    __tablename__ = "route_corners"

    id = Column(Integer, primary_key=True, index=True)
    route_id = Column(Integer, ForeignKey("routes.id"))
    corner_id = Column(Integer, ForeignKey("corners.id"))
    order = Column(Integer, default=0)

    route = relationship("Route", back_populates="corners")
    corner = relationship("Corner", back_populates="route_corners")


class Achievement(Base):
    __tablename__ = "achievements"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    icon = Column(String(100), default="🏆")
    condition_type = Column(String(50), nullable=False)
    condition_value = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    users = relationship("UserAchievement", back_populates="achievement")


class UserAchievement(Base):
    __tablename__ = "user_achievements"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    achievement_id = Column(Integer, ForeignKey("achievements.id"))
    unlocked_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="achievements")
    achievement = relationship("Achievement", back_populates="users")


class Share(Base):
    __tablename__ = "shares"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    content_type = Column(String(20), nullable=False)
    content_id = Column(Integer, nullable=False)
    platform = Column(String(50), default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="shares")


class Image(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    width = Column(Integer)
    height = Column(Integer)
    format = Column(String(20))
    thumb_small_url = Column(String(500))
    thumb_medium_url = Column(String(500))
    thumb_large_url = Column(String(500))
    original_url = Column(String(500))
    content_type = Column(String(100))
    is_public = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="images")

