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
import os
import logging
from celery_worker import validate_agent_config, notify_agent_ready
from contextvars import ContextVar
from fastapi import Request

# Request-scoped context variables
request_id_var: ContextVar[str] = ContextVar('request_id', default='unknown')
tenant_id_var: ContextVar[str] = ContextVar('tenant_id', default='unknown')

# Configure structured logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


app = FastAPI()

from fastapi import Request

@app.middleware("http")
async def add_request_context(request: Request, call_next):
    # Generate unique request ID
    req_id = str(uuid.uuid4())[:8]
    
    # Extract tenant_id from query params (for testing)
    # In production, extract from JWT token
    tenant_id = request.query_params.get('tenant_id', 'unknown')
    
    # Set context variables
    request_id_var.set(req_id)
    tenant_id_var.set(tenant_id)
    
    # Log request received (structured JSON)
    logger.info(json.dumps({
        "event": "request_received",
        "request_id": req_id,
        "tenant_id": tenant_id,
        "method": request.method,
        "path": request.url.path
    }))
    
    response = await call_next(request)
    return response

def log_with_context(event: str, **kwargs):
    """Log with request_id and tenant_id automatically included"""
    log_data = {
        "event": event,
        "request_id": request_id_var.get(),
        "tenant_id": tenant_id_var.get(),
    }
    log_data.update(kwargs)
    logger.info(json.dumps(log_data))

Base.metadata.create_all(bind=engine)
# Redis client


redis_host = os.getenv('REDIS_HOST', 'redis')
redis_client = redis.Redis(host=redis_host, port=6379, db=0, decode_responses=True)


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
    tenant_id = agent.tenant_id  # Source from request body, not context
    tenant_id_var.set(tenant_id)  # Update context so logs use correct tenant_id
    agent_id = str(uuid.uuid4())
    
    log_with_context("agent_creation_started", agent_name=agent.name, agent_id=agent_id)
    
    db_agent = AgentDB(
        id=agent_id,
        tenant_id=tenant_id,
        name=agent.name,
        image=agent.image,
        status=agent.status,
        config=agent.config,
        created_at=datetime.now().isoformat()
    )
    db.add(db_agent)
    db.commit()
    db.refresh(db_agent)
    
    log_with_context("agent_created_in_db", agent_id=agent_id)
    
    # Invalidate cache for this tenant
    cache_key = f"agents:{tenant_id}"
    redis_client.delete(cache_key)
    
    # Send Celery tasks
    validate_agent_config.delay(agent_id, tenant_id)
    notify_agent_ready.delay(agent_id, tenant_id)
    
    log_with_context("agent_creation_complete", agent_id=agent_id)
    
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