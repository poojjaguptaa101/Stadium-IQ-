"""
StadiumIQ — AI API Routes
All endpoints powered by Anthropic Claude with live sensor context.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from services.ai_service import (
    answer_query,
    get_route,
    generate_ai_recommendations,
    predict_exit_wave,
)

router = APIRouter()


class QueryRequest(BaseModel):
    query: str
    user_section: Optional[str] = "B"
    user_row: Optional[int] = 14


class RouteRequest(BaseModel):
    from_location: str
    to_location: str
    avoid_congestion: bool = True


@router.post("/ask", summary="Ask StadiumIQ AI anything about the venue")
def ask_ai(request: QueryRequest):
    """
    Natural language Q&A powered by Claude.
    The AI has access to live crowd, gate, and concession data.

    Example queries:
    - "Where's the nearest restroom?"
    - "Which gate has the shortest wait?"
    - "What food is available near me?"
    - "How do I get to Gate D from Section B?"
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    return answer_query(request.query, request.user_section, request.user_row)


@router.post("/route", summary="Get step-by-step navigation inside the venue")
def get_navigation(request: RouteRequest):
    """
    AI-powered in-venue navigation.
    Avoids congested zones when avoid_congestion=true.
    """
    return get_route(request.from_location, request.to_location, request.avoid_congestion)


@router.get("/recommendations", summary="Get proactive AI recommendations right now")
def ai_recommendations():
    """
    Claude analyses live sensor data and proactively generates
    crowd safety alerts, routing nudges, and experience improvements.
    """
    return {"recommendations": generate_ai_recommendations()}


@router.get("/predict-exit", summary="Predict exit wave and recommend strategy")
def exit_prediction(minutes_to_fulltime: int = Query(15, ge=1, le=120)):
    """
    Predicts the post-match crowd surge and recommends
    which gates to use and whether to leave early.
    """
    return predict_exit_wave(minutes_to_fulltime)
