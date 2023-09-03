from datetime import datetime, timezone

import sqlalchemy.engine
from sqlalchemy import (
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL: str = "postgresql://asd_motorart:asd_motorart@db:5432/asdmotorart"
local_timezone: datetime.tzinfo = datetime.now(timezone.utc).astimezone().tzinfo

# Create a SQLAlchemy engine and session
engine: sqlalchemy.engine.Engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False)

Base = declarative_base()

