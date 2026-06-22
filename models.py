from sqlalchemy import Column, String, JSON
from database import Base

class AgentDB(Base):
    __tablename__ = "agents"

    id = Column(String, primary_key=True)
    tenant_id = Column(String, nullable=False)
    name = Column(String, nullable=False)
    image = Column(String, nullable=False)
    status = Column(String, nullable=False)
    config = Column(JSON, nullable=False)
    created_at = Column(String, nullable=False)