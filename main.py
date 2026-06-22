from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
import uuid
from database import SessionLocal, engine
from models import AgentDB, Base
from fastapi import Depends
from sqlalchemy.orm import Session

app = FastAPI()

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



class Agent(BaseModel):
    id: Optional[str] = None
    tenant_id: str
    name: str
    image: str
    status: str
    config: dict
    created_at: Optional[str] = None


@app.post("/agents")
async def create_agent(agent: Agent, db: Session = Depends(get_db)):
    db_agent = AgentDB(
        id=str(uuid.uuid4()),
        tenant_id=agent.tenant_id,
        name=agent.name,
        image=agent.image,
        status=agent.status,
        config=agent.config,
        created_at=datetime.now().isoformat()
    )
    db.add(db_agent)
    db.commit()
    db.refresh(db_agent)
    return db_agent



@app.get("/agents/{agent_id}")
async def get_agent(agent_id: str, db: Session = Depends(get_db)):
    db_agent = db.query(AgentDB).filter(AgentDB.id == agent_id).first()
    if db_agent is None:
        return {"error": "Agent not found"}
    return db_agent

@app.put("/agents/{agent_id}")
async def update_agent(agent_id: str, agent: Agent, db: Session = Depends(get_db)):
    db_agent = db.query(AgentDB).filter(AgentDB.id == agent_id).first()
    if db_agent is None:
        return {"error": "Agent not found"}
    db_agent.name = agent.name
    db_agent.image = agent.image
    db_agent.status = agent.status
    db_agent.config = agent.config
    db.commit()
    db.refresh(db_agent)
    return db_agent

@app.delete("/agents/{agent_id}")
async def delete_agent(agent_id: str, db: Session = Depends(get_db)):
    db_agent = db.query(AgentDB).filter(AgentDB.id == agent_id).first()
    if db_agent is None:
        return {"error": "Agent not found"}
    db.delete(db_agent)
    db.commit()
    return {"message": "Agent deleted"}
@app.get("/agents")
async def list_agents(db: Session = Depends(get_db)):
    return db.query(AgentDB).all()