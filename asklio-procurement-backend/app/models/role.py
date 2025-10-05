from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.db.base import Base


class Role(Base):
    __tablename__ = "role"

    id = Column(Integer, primary_key=True)
    name = Column(String(64), unique=True, nullable=False)

    # reverse to UserRole join rows
    users = relationship("UserRole", back_populates="role", cascade="all, delete-orphan")