"""Anomaly detection API."""
from fastapi import APIRouter, Depends
from app.deps import get_current_user
from app.models import User
from app.services.anomaly_detection import AnomalyDetector

router = APIRouter(prefix="/anomalies", tags=["anomalies"])


@router.get("")
def list_anomalies(current_user: User = Depends(get_current_user)):
    return {"anomalies": AnomalyDetector.get_all_anomalies(user_id=current_user.id)}
