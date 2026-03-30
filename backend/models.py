from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, DateTime, JSON, Boolean, Float, ForeignKey,
)
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    garmin_credentials_encrypted = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    preferences = relationship(
        "UserPreferences", back_populates="user",
        uselist=False, cascade="all, delete-orphan",
    )
    schemas = relationship(
        "TrainingSchema", back_populates="user", cascade="all, delete-orphan",
    )


class UserPreferences(Base):
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    # ["maandag", "dinsdag", "woensdag", "donderdag", "vrijdag", "zaterdag", "zondag"]
    active_days = Column(JSON, default=list)
    long_run_day = Column(String, nullable=True)
    goal_distance = Column(String, nullable=True)   # "5K" | "10K" | "halve_marathon" | "marathon" | "custom"
    goal_distance_km = Column(Float, nullable=True)  # only when goal_distance == "custom"
    goal_pace = Column(String, nullable=True)        # "5:30" (min/km)
    goal_time = Column(String, nullable=True)        # "1:45:00"
    schema_type = Column(String, default="fixed")    # "fixed" | "rolling"
    schema_weeks = Column(Integer, default=12)       # only for fixed
    start_date = Column(String, nullable=True)       # ISO date "2026-04-07"

    user = relationship("User", back_populates="preferences")


class TrainingSchema(Base):
    __tablename__ = "training_schemas"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    schema_type = Column(String, nullable=False)   # "fixed" | "rolling"
    schema_data = Column(JSON, nullable=False)
    is_active = Column(Boolean, default=True)

    user = relationship("User", back_populates="schemas")
