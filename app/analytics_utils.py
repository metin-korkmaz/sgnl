from fastapi import Request, Response, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging

from analytics_middleware import get_db, get_client_ip, parse_device_type
from analytics_models import VisitorLog, PageView, AnalyticsEvent

logger = logging.getLogger(__name__)


async def create_visitor(request: Request, session_id: str):
    db: Session = next(get_db())
    
    try:
        ip = get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")
        referrer = request.headers.get("referer", "")
        landing_page = str(request.url.path)
        
        device_type = parse_device_type(user_agent)
        
        existing = db.query(VisitorLog).filter(
            VisitorLog.session_id == session_id
        ).first()
        
        if existing:
            return existing
        
        visitor = VisitorLog(
            session_id=session_id,
            ip_address=ip,
            user_agent=user_agent,
            device_type=device_type,
            referrer=referrer,
            landing_page=landing_page,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            is_active=True,
            total_time_seconds=0.0
        )
        
        db.add(visitor)
        db.commit()
        db.refresh(visitor)
        
        logger.info(f"[ANALYTICS] New visitor: {session_id} from {ip}")
        return visitor
        
    except Exception as e:
        logger.error(f"[ANALYTICS] Create visitor error: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


def cleanup_old_visitors(db: Session, days: int = 90):
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    deleted = db.query(VisitorLog).filter(
        VisitorLog.created_at < cutoff
    ).delete()
    
    deleted_pageviews = db.query(PageView).filter(
        PageView.created_at < cutoff
    ).delete()
    
    deleted_events = db.query(AnalyticsEvent).filter(
        AnalyticsEvent.created_at < cutoff
    ).delete()
    
    db.commit()
    
    logger.info(f"[ANALYTICS] Cleaned up {deleted} visitors, {deleted_pageviews} pageviews, {deleted_events} events older than {days} days")
    
    return {
        "visitors_deleted": deleted,
        "pageviews_deleted": deleted_pageviews,
        "events_deleted": deleted_events
    }
