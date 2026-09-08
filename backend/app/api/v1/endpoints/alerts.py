from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import Alert
from app.schemas.schemas import AlertResponse, AlertResolveRequest
from app.services.alert_service import alert_service

router = APIRouter()


@router.get("", response_model=List[AlertResponse])
@router.get("/", response_model=List[AlertResponse])
def get_alerts(
    status: Optional[str] = Query(None, description="Filter by status: ACTIVE, ACKNOWLEDGED, RESOLVED, or ALL"),
    severity: Optional[str] = Query(None, description="Filter by severity: CRITICAL, WARNING, INFO, RESOLVED, SYSTEM"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    query = db.query(Alert)

    if status and status.upper() != "ALL":
        query = query.filter(Alert.status == status.upper())

    if severity:
        query = query.filter(Alert.severity == severity.upper())

    alerts = query.order_by(Alert.created_at.desc()).limit(limit).all()
    return alerts


@router.get("/summary")
def get_alerts_summary(db: Session = Depends(get_db)):
    active_count = db.query(Alert).filter(Alert.status.in_(["ACTIVE", "ACKNOWLEDGED"])).count()
    critical_count = db.query(Alert).filter(Alert.status == "ACTIVE", Alert.severity == "CRITICAL").count()
    warning_count = db.query(Alert).filter(Alert.status == "ACTIVE", Alert.severity == "WARNING").count()

    return {
        "active_total": active_count,
        "critical_active": critical_count,
        "warning_active": warning_count,
        "badge_count": active_count
    }


@router.post("/{alert_id}/acknowledge", response_model=AlertResponse)
def acknowledge_alert(alert_id: int, user_name: str = "Administrator", db: Session = Depends(get_db)):
    alert = alert_service.acknowledge_alert(db=db, alert_id=alert_id, user_name=user_name)
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert #{alert_id} not found")
    return alert


@router.post("/{alert_id}/resolve", response_model=AlertResponse)
def resolve_alert(alert_id: int, payload: AlertResolveRequest, db: Session = Depends(get_db)):
    alert = alert_service.resolve_alert(
        db=db,
        alert_id=alert_id,
        resolved_by=payload.resolved_by,
        notes=payload.notes
    )
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert #{alert_id} not found")
    return alert
