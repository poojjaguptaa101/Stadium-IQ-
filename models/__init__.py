"""
StadiumIQ — Shared Pydantic models
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum
from datetime import datetime


class CongestionLevel(str, Enum):
    clear    = "clear"
    moderate = "moderate"
    high     = "high"
    critical = "critical"


class WaitLevel(str, Enum):
    low    = "low"
    medium = "medium"
    high   = "high"


# ── Crowd ────────────────────────────────────────────────────────────────────

class ZoneDensity(BaseModel):
    zone: str
    density_pct: float = Field(..., ge=0, le=100)
    capacity: int
    current_count: int
    level: CongestionLevel
    trend: str  # "rising" | "falling" | "stable"
    last_updated: datetime


class CrowdOverview(BaseModel):
    total_occupancy_pct: float
    total_attendees: int
    stadium_capacity: int
    zones: List[ZoneDensity]
    hotspot_zone: str
    safest_zone: str
    timestamp: datetime


# ── Gates ────────────────────────────────────────────────────────────────────

class GateStatus(BaseModel):
    gate_id: str
    name: str
    wait_minutes: int
    queue_length: int
    lanes_open: int
    lanes_total: int
    congestion: CongestionLevel
    throughput_per_min: int
    is_recommended: bool = False


class GatesOverview(BaseModel):
    gates: List[GateStatus]
    recommended_gate: str
    avg_wait_minutes: float
    timestamp: datetime


# ── Concessions ──────────────────────────────────────────────────────────────

class ConcessionStand(BaseModel):
    stand_id: str
    name: str
    location: str
    level: int
    gate_near: str
    wait_minutes: int
    wait_level: WaitLevel
    items_available: List[str]
    is_order_ahead: bool
    distance_meters: int


class ConcessionsOverview(BaseModel):
    stands: List[ConcessionStand]
    fastest_stand: str
    timestamp: datetime


# ── Alerts ───────────────────────────────────────────────────────────────────

class AlertSeverity(str, Enum):
    info     = "info"
    warning  = "warning"
    critical = "critical"
    success  = "success"


class Alert(BaseModel):
    alert_id: str
    title: str
    description: str
    severity: AlertSeverity
    source: str
    location: Optional[str] = None
    timestamp: datetime
    is_ai_generated: bool = False
    action_label: Optional[str] = None


# ── AI ───────────────────────────────────────────────────────────────────────

class AIQueryRequest(BaseModel):
    query: str
    user_section: Optional[str] = "B"
    user_row: Optional[int] = 14
    context: Optional[str] = None


class AIQueryResponse(BaseModel):
    answer: str
    recommendations: List[str]
    confidence: float
    timestamp: datetime


class RouteRequest(BaseModel):
    from_location: str
    to_location: str
    avoid_congestion: bool = True


class RouteResponse(BaseModel):
    steps: List[str]
    estimated_minutes: int
    congestion_avoided: bool
    timestamp: datetime


# ── Events ───────────────────────────────────────────────────────────────────

class LiveEvent(BaseModel):
    event_id: str
    name: str
    venue: str
    sport: str
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    status: str
    period: str
    start_time: datetime
    section: str
    row: int
