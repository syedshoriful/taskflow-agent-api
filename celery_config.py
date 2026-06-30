import os
from celery import Celery

# Create Celery app instance
app = Celery('taskflow')

# Allow override via env vars (for CI), default to Docker service names
rabbitmq_host = os.getenv('RABBITMQ_HOST', 'rabbitmq')
redis_host = os.getenv('REDIS_HOST', 'redis')

# Connect to RabbitMQ (message broker)
app.conf.broker_url = f'amqp://guest:guest@{rabbitmq_host}:5672//'

# Store results in Redis (result backend)
app.conf.result_backend = f'redis://{redis_host}:6379/0'