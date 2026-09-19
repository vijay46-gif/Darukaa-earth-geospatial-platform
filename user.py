import datetime

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from app.database.session import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default="user", nullable=False)  # admin, manager, user
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    projects = relationship("Project", back_populates="creator", cascade="all, delete-orphan")
    activities = relationship("ActivityLog", back_populates="user")
