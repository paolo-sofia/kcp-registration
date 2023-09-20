from datetime import datetime, timezone

import sqlalchemy.engine
import tomli
from sqlalchemy import (
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

with open("data/secrets.toml", "rb") as f:
    config = tomli.load(f)["database"]

DATABASE_URL: str = f"postgresql://{config['user']}:{config['password']}@db:5432/{config['database']}"
local_timezone: datetime.tzinfo = datetime.now(timezone.utc).astimezone().tzinfo

# Create a SQLAlchemy engine and session
engine: sqlalchemy.engine.Engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False)

Base = declarative_base()
