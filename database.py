from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DATABASE_URL = "postgresql://syedshorifulalamopu@localhost/taskflow_db"

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(bind=engine)

class Base(DeclarativeBase):
    pass