from fastapi import APIRouter
from services.sensor_sim import get_crowd_data

router = APIRouter()

@router.get("/", summary="Live crowd density across all zones")
def crowd_overview():
    return get_crowd_data()

@router.get("/{zone}", summary="Crowd density for a specific zone")
def zone_density(zone: str):
    data = get_crowd_data()
    match = next((z for z in data["zones"] if z["zone"].lower() == zone.lower()), None)
    if not match:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Zone '{zone}' not found")
    return match
