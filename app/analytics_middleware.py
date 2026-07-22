from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
import logging

from analytics_models import Base, VisitorLog
from config import config

logger = logging.getLogger(__name__)

# Lazy load database engine to avoid circular import issues
_engine = None
_SessionLocal = None


def get_engine():
    global _engine, _SessionLocal
    if _engine is None:
        _engine = create_engine(config.DATABASE_URL)
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    return _engine


def get_session_local():
    get_engine()
    return _SessionLocal


def get_db():
    db = get_session_local()()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=get_engine())
    logger.info("[ANALYTICS] Database initialized")


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def parse_device_type(user_agent_str: str) -> str:
    if not user_agent_str:
        return "unknown"
    
    ua = user_agent_str.lower()
    
    if "mobile" in ua or "android" in ua or "iphone" in ua:
        return "mobile"
    elif "ipad" in ua or "tablet" in ua:
        return "tablet"
    elif "windows" in ua or "macintosh" in ua or "linux" in ua:
        return "desktop"
    elif "bot" in ua or "spider" in ua or "crawl" in ua:
        return "bot"
    else:
        return "unknown"


class AnalyticsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        db: Session = get_session_local()()

        try:
            ip = get_client_ip(request)
            ua = request.headers.get("user-agent", "")
            referrer = request.headers.get("referer", "")

            session_id = request.cookies.get("sgnl_session")

            if session_id:
                # Optimized query with composite index
                visitor = db.query(VisitorLog).filter(
                    VisitorLog.session_id == session_id,
                    VisitorLog.is_active == True
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
