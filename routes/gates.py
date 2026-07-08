from fastapi import APIRouter, HTTPException
from services.sensor_sim import get_gate_data

router = APIRouter()

@router.get("/", summary="All gate statuses with wait times")
def gates_overview():
    return get_gate_data()

@router.get("/recommended", summary="Get the least congested gate right now")
def recommended_gate():
    data = get_gate_data()
    gate = next((g for g in data["gates"] if g["is_recommended"]), None)
    return {"recommended_gate": gate, "timestamp": data["timestamp"]}

@router.get("/{gate_id}", summary="Status of a specific gate")
def gate_detail(gate_id: str):
    data = get_gate_data()
    gate = next(
        (g for g in data["gates"] if g["gate_id"] == gate_id.lower().replace(" ", "_")),
        None
    )
    if not gate:
        raise HTTPException(status_code=404, detail=f"Gate '{gate_id}' not found")
    return gate
