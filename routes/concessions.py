from fastapi import APIRouter, Query
from services.sensor_sim import get_concessions_data

router = APIRouter()

@router.get("/", summary="All concession stands with wait times")
def concessions_overview():
    return get_concessions_data()

@router.get("/fastest", summary="Get the stand with the shortest wait")
def fastest_stand():
    data = get_concessions_data()
    return {
        "fastest_stand": data["stands"][0] if data["stands"] else None,
        "timestamp": data["timestamp"],
    }

@router.get("/by-gate/{gate}", summary="Stands near a specific gate")
def stands_by_gate(gate: str):
    data = get_concessions_data()
    filtered = [s for s in data["stands"] if s["gate_near"].upper() == gate.upper()]
    return {"stands": filtered, "timestamp": data["timestamp"]}
