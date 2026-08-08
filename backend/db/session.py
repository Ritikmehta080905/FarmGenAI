from database.db import engine, AsyncSessionLocal
from sqlalchemy.orm import declarative_base

Base = declarative_base()
