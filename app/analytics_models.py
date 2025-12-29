from sqlalchemy import Column, Integer, String, DateTime, Float, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()


class VisitorLog(Base):
    __tablename__ = "visitor_logs"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), unique=True, index=True, nullable=False)
    ip_address = Column(String(50), index=True, nullable=False)
    user_agent = Column(Text)
    device_type = Column(String(20))
    country = Column(String(50))
    city = Column(String(100))
    referrer = Column(Text)
    landing_page = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    last_activity = Column(DateTime, default=datetime.utcnow, index=True)
    is_active = Column(Boolean, default=True)
    total_time_seconds = Column(Float, default=0.0)


class PageView(Base):
    __tablename__ = "page_views"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), index=True, nullable=False)
    path = Column(String(500), nullable=False)
    query_params = Column(Text)
    time_on_page = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), index=True, nullable=False)
    event_type = Column(String(50), nullable=False, index=True)
    event_data = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
