from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base

class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True, index=True)
    firstname = Column(String(120), nullable=False)
    lastname = Column(String(120), nullable=False)
    username = Column(String(120), unique=True, index=True, nullable=False)
    hashedPassword = Column(String(255), nullable=False)
    departmentID = Column(Integer, ForeignKey("department.id"))
    department = relationship("Department", back_populates="users")
    roles = relationship("UserRole", back_populates="user")
    requests = relationship("ProcurementRequest", back_populates="created_by")