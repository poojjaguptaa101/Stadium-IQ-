from fastapi import APIRouter
from services.sensor_sim import get_live_event

router = APIRouter()

@router.get("/live", summary="Current live event details and score")
def live_event():
    return get_live_event()
