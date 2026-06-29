from fastapi import FastAPI, Depends
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import uuid
from database import SessionLocal, engine
from models import AgentDB, User, Base
from sqlalchemy.orm import Session
from auth import hash_password, verify_password, create_access_token, verify_access_token
import redis
import json
app = FastAPI()

Base.metadata.create_all(bind=engine)
# Redis client
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Pydantic schemas
class Agent(BaseModel):
    id: Optional[str] = None
    tenant_id: str
    name: str
    image: str
    status: str
    config: dict
    created_at: Optional[str] = None


class UserSignup(BaseModel):
    email: str
    password: str
    tenant_id: str


class UserLogin(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    tenant_id: str

def cache_agent_list(tenant_id: str, agents: list) -> None:
    """Cache agent list in Redis with 5-minute TTL."""
    cache_key = f"agents:{tenant_id}"
    cache_value = json.dumps([{
        "id": a.id,
        "tenant_id": a.tenant_id,
        "name": a.name,
        "image": a.image,
        "status": a.status,
        "config": a.config,
        "created_at": a.created_at
    } for a in agents])
    redis_client.set(cache_key, cache_value, ex=300)  # 5 min TTL
    
@app.get("/agents/{agent_id}")
async def get_agent(agent_id: str, db: Session = Depends(get_db)):
    db_agent = db.query(AgentDB).filter(AgentDB.id == agent_id).first()
    if db_agent is None:
        return {"error": "Agent not found"}
    return db_agent

# Agent CRUD endpoints
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
    
    # Invalidate cache for this tenant
    cache_key = f"agents:{agent.tenant_id}"
    redis_client.delete(cache_key)
    
    return db_agent



@app.get("/agents")
async def list_agents(tenant_id: str, db: Session = Depends(get_db)):
    cache_key = f"agents:{tenant_id}"
    
    # Check Redis cache first
    cached = redis_client.get(cache_key)
    
    if cached:
        return json.loads(cached)
    
    # Cache miss: query DB
    agents = db.query(AgentDB).filter(AgentDB.tenant_id == tenant_id).all()
    
    
    # Cache the result
    if agents:
        cache_agent_list(tenant_id, agents)
    
    
    return agents

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

    # Invalidate cache for this tenantß
    redis_client.delete(f"agents:{db_agent.tenant_id}")

    return db_agent


@app.delete("/agents/{agent_id}")
async def delete_agent(agent_id: str, db: Session = Depends(get_db)):
    db_agent = db.query(AgentDB).filter(AgentDB.id == agent_id).first()
    if db_agent is None:
        return {"error": "Agent not found"}
    db.delete(db_agent)
    db.commit()
    
    # Invalidate cache for this tenant
    redis_client.delete(f"agents:{db_agent.tenant_id}")
    
    return {"message": "Agent deleted"}
    


# Authentication endpoints
@app.post("/signup")
async def signup(user_data: UserSignup, db: Session = Depends(get_db)):
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        return {"error": "Email already registered"}
    
    # Hash the password
    hashed_pwd = hash_password(user_data.password)
    
    # Create new user
    new_user = User(
        id=str(uuid.uuid4()),
        tenant_id=user_data.tenant_id,
        email=user_data.email,
        hashed_password=hashed_pwd
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {"message": "User created", "email": new_user.email, "tenant_id": new_user.tenant_id}


@app.post("/login")
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    # Find user by email
    user = db.query(User).filter(User.email == user_data.email).first()
    if not user:
        return {"error": "Invalid email or password"}
    
    # Verify password
    if not verify_password(user_data.password, user.hashed_password):
        return {"error": "Invalid email or password"}
    
    # Create JWT token
    token_data = {
        "sub": user.email,
        "user_id": user.id,
        "tenant_id": user.tenant_id
    }
    access_token = create_access_token(token_data)
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        tenant_id=user.tenant_id
    )