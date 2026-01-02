"""
sql/database.py

Crea el engine async de SQLAlchemy.

IMPORTANTE:
- 'check_same_thread' SOLO existe para SQLite.
- Si lo pasas a Postgres/asyncpg, el arranque de la BD puede fallar.
"""
import os

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.engine.url import make_url


SQLALCHEMY_DATABASE_URL = os.getenv(
    "SQLALCHEMY_DATABASE_URL",
    "sqlite+aiosqlite:///./auth.db",
)

_url = make_url(SQLALCHEMY_DATABASE_URL)

connect_args = {}
if _url.get_backend_name() == "sqlite":
    connect_args = {"check_same_thread": False}

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=False,
    connect_args=connect_args,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession,
    future=True,
)

Base = declarative_base()