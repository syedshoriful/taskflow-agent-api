from celery_config import app
import time
from datetime import datetime

@app.task
def validate_agent_config(agent_id: str, tenant_id: str):
    """
    Async task: validate agent configuration
    Runs in background on Celery worker
    """
    print(f"[CELERY] Validating agent {agent_id} for tenant {tenant_id}")
    
    # Simulate validation (takes 5 seconds)
    time.sleep(5)
    
    return {
        "agent_id": agent_id,
        "tenant_id": tenant_id,
        "status": "validated",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.task
def notify_agent_ready(agent_id: str, tenant_id: str):
    """
    Async task: notify that agent is ready
    Runs in background on Celery worker
    """
    print(f"[CELERY] Agent {agent_id} is ready for tenant {tenant_id}")
    
    # Simulate notification (takes 2 seconds)
    time.sleep(2)
    
    return {
        "agent_id": agent_id,
        "status": "notified"
    }