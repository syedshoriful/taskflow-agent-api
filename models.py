from sqlalchemy import Column, String, JSON, DateTime
from database import Base
from uuid import uuid4
from datetime import datetime
class AgentDB(Base):
    __tablename__ = "agents"

    id = Column(String, primary_key=True)
    tenant_id = Column(String, nullable=False)
    name = Column(String, nullable=False)
    image = Column(String, nullable=False)
    status = Column(String, nullable=False)
    config = Column(JSON, nullable=False)
    created_at = Column(String, nullable=False)


class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    tenant_id = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)