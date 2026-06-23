from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
import os 


database_url = os.getenv("DATABASE_URL", "postgresql://syedshorifulalamopu@localhost/taskflow_db")
engine = create_engine(database_url)

SessionLocal = sessionmaker(bind=engine)

class Base(DeclarativeBase):
    pass