from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import app, get_db
from models import Base

# Create in-memory SQLite database for testing
SQLALCHEMY_TEST_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_TEST_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(bind=engine)
Base.metadata.create_all(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

def test_create_agent():
    response = client.post("/agents", json={
        "tenant_id": "acme",
        "name": "test-agent",
        "image": "nginx:latest",
        "status": "pending",
        "config": {}
    })
    assert response.status_code == 200
    assert response.json()["tenant_id"] == "acme"
    assert response.json()["name"] == "test-agent"

def test_list_agents():
    response = client.get("/agents")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_agent_not_found():
    response = client.get("/agents/nonexistent-id")
    assert response.status_code == 200
    assert response.json()["error"] == "Agent not found"