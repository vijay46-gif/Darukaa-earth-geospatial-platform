import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database.session import Base


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(
        String(100), nullable=False
    )  # e.g. "Project Created", "Site Added", "User Login"
    entity_type = Column(String(50), nullable=False)  # "Project", "Site", "User", "System"
    entity_id = Column(Integer, nullable=True)
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False, index=True)

    user = relationship("User", back_populates="activities")
