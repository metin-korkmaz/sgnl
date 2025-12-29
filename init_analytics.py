#!/usr/bin/env python3
"""
Initialize analytics database for SGNL.
Run this script to create the database tables.
"""

import os
import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.analytics_models import Base

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./analytics.db")

print(f"Using database: {DATABASE_URL}")

engine = create_engine(DATABASE_URL)
Base.metadata.create_all(bind=engine)

print("✓ Database tables created successfully")
print("✓ Analytics system ready")
