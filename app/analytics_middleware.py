from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
import user_agent
import logging
import os

from analytics_models import Base, VisitorLog

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./analytics.db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
    logger.info("[ANALYTICS] Database initialized")


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def parse_device_type(user_agent_str: str) -> str:
    if not user_agent_str:
        return "unknown"
    
    ua = user_agent.parse(user_agent_str)
    
    if ua.is_mobile:
        return "mobile"
    elif ua.is_tablet:
        return "tablet"
    elif ua.is_pc:
        return "desktop"
    else:
        return "bot"


class AnalyticsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        db: Session = SessionLocal()
        
        try:
            ip = get_client_ip(request)
            ua = request.headers.get("user-agent", "")
            referrer = request.headers.get("referer", "")
            
            session_id = request.cookies.get("sgnl_session")
            
            if session_id:
                visitor = db.query(VisitorLog).filter(
                    VisitorLog.session_id == session_id
                ).first()
                
                if visitor:
                    visitor.last_activity = datetime.utcnow()
                    
                    if referrer and not visitor.referrer:
                        visitor.referrer = referrer
                    
                    db.commit()
            
            response = await call_next(request)
            
            return response
            
        except Exception as e:
            logger.error(f"[ANALYTICS] Middleware error: {e}")
            return await call_next(request)
        finally:
            db.close()
