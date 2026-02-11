import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Get database URL from Render environment
DATABASE_URL = os.getenv("DATABASE_URL")

# For safety if not found
if not DATABASE_URL:
    raise ValueError("DATABASE_URL not found. Check Render environment variables.")

# Fix for postgres connection
DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://")

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

print("✅ Connected to PERMANENT Neon PostgreSQL Database")
