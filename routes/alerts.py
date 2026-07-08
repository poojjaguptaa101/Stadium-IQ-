from fastapi import APIRouter, Query
from services.sensor_sim import get_alerts_data

router = APIRouter()

@router.get("/", summary="All active alerts and notifications")
def all_alerts(severity: str = Query(None, description="Filter by severity: info|warning|critical|success")):
    alerts = get_alerts_data()
    if severity:
        alerts = [a for a in alerts if a["severity"] == severity]
    return {"alerts": alerts, "count": len(alerts)}

@router.get("/critical", summary="Only critical alerts")
def critical_alerts():
    alerts = [a for a in get_alerts_data() if a["severity"] == "critical"]
    return {"alerts": alerts, "count": len(alerts)}
