from celery_config import app
import time
from datetime import datetime
import logging
import json
from contextvars import ContextVar

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(message)s')

# Context variables for Celery tasks
request_id_var: ContextVar[str] = ContextVar('request_id', default='celery-task')
tenant_id_var: ContextVar[str] = ContextVar('tenant_id', default='unknown')

def log_with_context(event: str, **kwargs):
    """Log with request_id and tenant_id for Celery tasks"""
    log_data = {
        "event": event,
        "request_id": request_id_var.get(),
        "tenant_id": tenant_id_var.get(),
    }
    log_data.update(kwargs)
    logger.info(json.dumps(log_data))

@app.task
def validate_agent_config(agent_id: str, tenant_id: str):
    """Validate agent configuration"""
    # Set context for this task
    tenant_id_var.set(tenant_id)
    request_id_var.set(f"celery-{agent_id[:8]}")
    
    log_with_context("validation_started", agent_id=agent_id)
    
    # Simulate validation (takes 5 seconds)
    time.sleep(5)
    
    log_with_context("validation_complete", agent_id=agent_id, status="passed")
    
    return {
        "agent_id": agent_id,
        "tenant_id": tenant_id,
        "status": "validated",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.task
def notify_agent_ready(agent_id: str, tenant_id: str):
    """Notify that agent is ready"""
    # Set context for this task
    tenant_id_var.set(tenant_id)
    request_id_var.set(f"celery-{agent_id[:8]}")
    
    log_with_context("notification_started", agent_id=agent_id)
    
    # Simulate notification (takes 2 seconds)
    time.sleep(2)
    
    log_with_context("notification_complete", agent_id=agent_id)
    
    return {
        "agent_id": agent_id,
        "status": "notified"
    }