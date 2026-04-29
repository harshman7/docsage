"""Anomaly detection API."""
from fastapi import APIRouter
from app.services.anomaly_detection import AnomalyDetector

router = APIRouter(prefix="/anomalies", tags=["anomalies"])


@router.get("")
def list_anomalies():
    return {"anomalies": AnomalyDetector.get_all_anomalies()}
