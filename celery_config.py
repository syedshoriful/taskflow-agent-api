from celery import Celery

# Create Celery app instance
app = Celery('taskflow')

# Connect to RabbitMQ (message broker)
app.conf.broker_url = 'amqp://guest:guest@rabbitmq:5672//'

# Store results in Redis (result backend)
app.conf.result_backend = 'redis://redis:6379/0'