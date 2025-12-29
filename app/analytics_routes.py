from fastapi import APIRouter, HTTPException, Request, Response, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
import logging

from analytics_middleware import get_db
from analytics_models import VisitorLog, PageView, AnalyticsEvent
from analytics_utils import cleanup_old_visitors

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analytics", tags=["analytics"])


class TrackEventRequest(BaseModel):
    session_id: str
    event_type: str
    event_data: Optional[str] = None


class HeartbeatRequest(BaseModel):
    session_id: str
    path: str


class PageViewRequest(BaseModel):
    session_id: str
    path: str
    time_on_page: Optional[float] = None


@router.post("/track")
async def track_event(req: TrackEventRequest, db: Session = Depends(get_db)):
    try:
        event = AnalyticsEvent(
            session_id=req.session_id,
            event_type=req.event_type,
            event_data=req.event_data,
            created_at=datetime.utcnow()
        )
        db.add(event)
        db.commit()
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"[ANALYTICS] Track error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/heartbeat")
async def heartbeat(req: HeartbeatRequest, db: Session = Depends(get_db)):
    try:
        visitor = db.query(VisitorLog).filter(
            VisitorLog.session_id == req.session_id
        ).first()
        
        if visitor:
            visitor.last_activity = datetime.utcnow()
            db.commit()
        
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"[ANALYTICS] Heartbeat error: {e}")
        return {"status": "ok"}


@router.post("/pageview")
async def record_pageview(req: PageViewRequest, db: Session = Depends(get_db)):
    try:
        pageview = PageView(
            session_id=req.session_id,
            path=req.path,
            time_on_page=req.time_on_page,
            created_at=datetime.utcnow()
        )
        db.add(pageview)
        db.commit()
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"[ANALYTICS] Pageview error: {e}")
        return {"status": "ok"}


@router.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    try:
        now = datetime.utcnow()
        last_7_days = now - timedelta(days=7)
        last_30_days = now - timedelta(days=30)
        
        total_visitors = db.query(func.count(VisitorLog.id)).scalar()
        unique_ips = db.query(func.count(func.distinct(VisitorLog.ip_address))).scalar()
        
        visitors_7d = db.query(func.count(VisitorLog.id)).filter(
            VisitorLog.created_at >= last_7_days
        ).scalar()
        
        visitors_30d = db.query(func.count(VisitorLog.id)).filter(
            VisitorLog.created_at >= last_30_days
        ).scalar()
        
        total_pageviews = db.query(func.count(PageView.id)).scalar()
        
        avg_time = db.query(func.avg(VisitorLog.total_time_seconds)).scalar() or 0
        
        device_breakdown = db.query(
            VisitorLog.device_type,
            func.count(VisitorLog.id)
        ).group_by(VisitorLog.device_type).all()
        
        top_pages = db.query(
            PageView.path,
            func.count(PageView.id).label('count')
        ).group_by(PageView.path).order_by(desc('count')).limit(10).all()
        
        return {
            "total_visitors": total_visitors,
            "unique_ips": unique_ips,
            "visitors_last_7_days": visitors_7d,
            "visitors_last_30_days": visitors_30d,
            "total_pageviews": total_pageviews,
            "avg_session_time_seconds": round(avg_time, 2),
            "device_breakdown": {k: v for k, v in device_breakdown},
            "top_pages": [{"path": p, "views": c} for p, c in top_pages]
        }
    except Exception as e:
        logger.error(f"[ANALYTICS] Stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/visitors")
async def get_visitors(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    try:
        visitors = db.query(VisitorLog).order_by(
            desc(VisitorLog.created_at)
        ).limit(limit).offset(offset).all()
        
        return {
            "visitors": [
                {
                    "session_id": v.session_id,
                    "ip_address": v.ip_address,
                    "user_agent": v.user_agent[:100] if v.user_agent else None,
                    "device_type": v.device_type,
                    "country": v.country,
                    "referrer": v.referrer,
                    "landing_page": v.landing_page,
                    "created_at": v.created_at.isoformat(),
                    "last_activity": v.last_activity.isoformat(),
                    "total_time_seconds": v.total_time_seconds
                }
                for v in visitors
            ],
            "total": db.query(func.count(VisitorLog.id)).scalar()
        }
    except Exception as e:
        logger.error(f"[ANALYTICS] Visitors error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup")
async def cleanup_data(days: int = 90, db: Session = Depends(get_db)):
    try:
        result = cleanup_old_visitors(db, days)
        return {"status": "ok", "deleted": result}
    except Exception as e:
        logger.error(f"[ANALYTICS] Cleanup error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
