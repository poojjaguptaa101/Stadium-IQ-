"""
StadiumIQ — Sensor Simulation Service
Simulates real-time BLE/Wi-Fi crowd sensor data for demo purposes.
In production this would connect to actual venue IoT infrastructure.
"""

import random
import math
from datetime import datetime
from typing import Dict, Tuple

# Stadium config
STADIUM_CAPACITY = 33_000
ZONES = {
    "North":  {"capacity": 9000,  "base_density": 82, "volatility": 6},
    "East":   {"capacity": 7000,  "base_density": 34, "volatility": 8},
    "West":   {"capacity": 7000,  "base_density": 58, "volatility": 7},
    "South":  {"capacity": 10000, "base_density": 28, "volatility": 5},
}

GATES = {
    "Gate A": {"base_wait": 2,  "lanes": 6, "total_lanes": 6},
    "Gate B": {"base_wait": 9,  "lanes": 4, "total_lanes": 6},
    "Gate C": {"base_wait": 16, "lanes": 3, "total_lanes": 6},
    "Gate D": {"base_wait": 1,  "lanes": 6, "total_lanes": 6},
    "Gate E": {"base_wait": 5,  "lanes": 5, "total_lanes": 6},
}

CONCESSION_STANDS = [
    {"id": "s001", "name": "Biryani House",   "gate": "B", "level": 1, "base_wait": 2,  "items": ["Biryani", "Raita", "Lassi"]},
    {"id": "s002", "name": "Burger Co.",      "gate": "C", "level": 2, "base_wait": 18, "items": ["Burgers", "Fries", "Shakes"]},
    {"id": "s003", "name": "Chai & Snacks",   "gate": "A", "level": 1, "base_wait": 1,  "items": ["Chai", "Samosa", "Vada Pav"]},
    {"id": "s004", "name": "Pizza Zone",      "gate": "D", "level": 3, "base_wait": 8,  "items": ["Pizza", "Garlic Bread", "Pasta"]},
    {"id": "s005", "name": "Fresh Juice Bar", "gate": "E", "level": 1, "base_wait": 3,  "items": ["Juices", "Smoothies", "Coconut Water"]},
    {"id": "s006", "name": "Ice Cream Stand", "gate": "A", "level": 2, "base_wait": 7,  "items": ["Ice Cream", "Gelato", "Kulfi"]},
]

_noise_offset = 0.0  # incremented each tick for wave-like noise


def _wave_noise(base: float, volatility: float, offset: float) -> float:
    """Sinusoidal noise to simulate realistic sensor fluctuation."""
    wave = math.sin(offset) * volatility * 0.5
    rand = random.uniform(-volatility * 0.3, volatility * 0.3)
    return max(0, min(100, base + wave + rand))


def _density_to_level(pct: float) -> str:
    if pct >= 80:  return "critical"
    if pct >= 60:  return "high"
    if pct >= 40:  return "moderate"
    return "clear"


def _wait_to_level(minutes: int) -> str:
    if minutes >= 12:  return "high"
    if minutes >= 6:   return "medium"
    return "low"


def _congestion_to_level(wait: int) -> str:
    if wait >= 12:  return "critical"
    if wait >= 7:   return "high"
    if wait >= 4:   return "moderate"
    return "clear"


def get_crowd_data() -> Dict:
    global _noise_offset
    _noise_offset += 0.15

    zones = []
    total_count = 0
    worst_zone = ("", 0)
    safest_zone = ("", 100)

    for zone_name, cfg in ZONES.items():
        density = round(_wave_noise(cfg["base_density"], cfg["volatility"], _noise_offset), 1)
        count = int(cfg["capacity"] * density / 100)
        total_count += count
        level = _density_to_level(density)

        prev = cfg["base_density"]
        trend = "rising" if density > prev + 2 else "falling" if density < prev - 2 else "stable"

        zones.append({
            "zone": zone_name,
            "density_pct": density,
            "capacity": cfg["capacity"],
            "current_count": count,
            "level": level,
            "trend": trend,
            "last_updated": datetime.now().isoformat(),
        })

        if density > worst_zone[1]:
            worst_zone = (zone_name, density)
        if density < safest_zone[1]:
            safest_zone = (zone_name, density)

    occupancy_pct = round(total_count / STADIUM_CAPACITY * 100, 1)

    return {
        "total_occupancy_pct": occupancy_pct,
        "total_attendees": total_count,
        "stadium_capacity": STADIUM_CAPACITY,
        "zones": zones,
        "hotspot_zone": worst_zone[0],
        "safest_zone": safest_zone[0],
        "timestamp": datetime.now().isoformat(),
    }


def get_gate_data() -> Dict:
    gates = []
    recommended = None
    min_wait = 9999

    for gate_name, cfg in GATES.items():
        jitter = random.randint(-2, 3)
        wait = max(1, cfg["base_wait"] + jitter)
        queue = wait * random.randint(8, 14)
        throughput = random.randint(18, 28)
        level = _congestion_to_level(wait)

        if wait < min_wait:
            min_wait = wait
            recommended = gate_name

        gates.append({
            "gate_id": gate_name.lower().replace(" ", "_"),
            "name": gate_name,
            "wait_minutes": wait,
            "queue_length": queue,
            "lanes_open": cfg["lanes"],
            "lanes_total": cfg["total_lanes"],
            "congestion": level,
            "throughput_per_min": throughput,
            "is_recommended": False,
        })

    for g in gates:
        g["is_recommended"] = (g["name"] == recommended)

    avg_wait = round(sum(g["wait_minutes"] for g in gates) / len(gates), 1)

    return {
        "gates": gates,
        "recommended_gate": recommended,
        "avg_wait_minutes": avg_wait,
        "timestamp": datetime.now().isoformat(),
    }


def get_concessions_data() -> Dict:
    stands = []
    fastest = None
    min_wait = 9999

    for s in CONCESSION_STANDS:
        jitter = random.randint(-2, 4)
        wait = max(1, s["base_wait"] + jitter)
        level = _wait_to_level(wait)
        distance = random.randint(40, 200)

        if wait < min_wait:
            min_wait = wait
            fastest = s["name"]

        stands.append({
            "stand_id": s["id"],
            "name": s["name"],
            "location": f"Gate {s['gate']} · Level {s['level']}",
            "level": s["level"],
            "gate_near": s["gate"],
            "wait_minutes": wait,
            "wait_level": level,
            "items_available": s["items"],
            "is_order_ahead": s["level"] == 1,
            "distance_meters": distance,
        })

    return {
        "stands": sorted(stands, key=lambda x: x["wait_minutes"]),
        "fastest_stand": fastest,
        "timestamp": datetime.now().isoformat(),
    }


def get_alerts_data() -> list:
    base_alerts = [
        {
            "alert_id": "a001",
            "title": "Medical team dispatched to Section F",
            "description": "First aid response in progress. Area temporarily cordoned.",
            "severity": "critical",
            "source": "Ops team",
            "location": "Section F",
            "timestamp": datetime.now().isoformat(),
            "is_ai_generated": False,
            "action_label": "View on map",
        },
        {
            "alert_id": "a002",
            "title": "Gate C reduced to 4 lanes",
            "description": "Two scanner lanes temporarily offline for maintenance. Expect higher wait times.",
            "severity": "warning",
            "source": "Gate ops",
            "location": "Gate C",
            "timestamp": datetime.now().isoformat(),
            "is_ai_generated": False,
            "action_label": "Redirect via Gate D",
        },
        {
            "alert_id": "a003",
            "title": "VIP Box 3 upgrade confirmed",
            "description": "Your seat upgrade request has been approved. Proceed to VIP Gate.",
            "severity": "success",
            "source": "Booking system",
            "location": "VIP Box 3",
            "timestamp": datetime.now().isoformat(),
            "is_ai_generated": False,
            "action_label": None,
        },
        {
            "alert_id": "a004",
            "title": "Parking Lot B is full",
            "description": "AI routing recommends using Lot D with free shuttle service.",
            "severity": "info",
            "source": "Parking AI",
            "location": "Lot B",
            "timestamp": datetime.now().isoformat(),
            "is_ai_generated": True,
            "action_label": "Get directions",
        },
        {
            "alert_id": "a005",
            "title": "Biryani House order delivered",
            "description": "Your pre-order has been delivered to Row 14, Section B.",
            "severity": "success",
            "source": "Concessions",
            "location": "Section B Row 14",
            "timestamp": datetime.now().isoformat(),
            "is_ai_generated": False,
            "action_label": None,
        },
    ]
    return base_alerts


def get_live_event() -> Dict:
    score_delta = random.randint(0, 2)
    return {
        "event_id": "evt_001",
        "name": "IPL 2026 — Match 38",
        "venue": "Wankhede Stadium, Mumbai",
        "sport": "cricket",
        "home_team": "Mumbai Indians",
        "away_team": "Chennai Super Kings",
        "home_score": 186 + score_delta,
        "away_score": 142,
        "status": "live",
        "period": "47th over",
        "start_time": datetime.now().isoformat(),
        "section": "B",
        "row": 14,
    }
