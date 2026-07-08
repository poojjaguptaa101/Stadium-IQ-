"""
╔══════════════════════════════════════════════════════════════════╗
║         StadiumIQ — AI-Powered Smart Venue Experience            ║
║         Full Stack · Single File · Python + FastAPI              ║
║                                                                  ║
║  Run:  pip install fastapi uvicorn anthropic                     ║
║        python stadiumiq_full.py                                  ║
║  Open: http://localhost:8000                                     ║
╚══════════════════════════════════════════════════════════════════╝
"""

import os, json, math, random
from datetime import datetime
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn

try:
    from anthropic import Anthropic
    _anthropic_client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
    AI_ENABLED = True
except Exception:
    _anthropic_client = None
    AI_ENABLED = False


# ═══════════════════════════════════════════════════════════════════
#  SENSOR SIMULATION  (replace with real IoT feeds in production)
# ═══════════════════════════════════════════════════════════════════

STADIUM_CAPACITY = 33_000
_tick = 0.0

ZONES_CFG = {
    "North": {"cap": 9000,  "base": 82, "vol": 6},
    "East":  {"cap": 7000,  "base": 34, "vol": 8},
    "West":  {"cap": 7000,  "base": 58, "vol": 7},
    "South": {"cap": 10000, "base": 28, "vol": 5},
}
GATES_CFG = {
    "Gate A": {"base_wait": 2,  "lanes": 6, "total": 6},
    "Gate B": {"base_wait": 9,  "lanes": 4, "total": 6},
    "Gate C": {"base_wait": 16, "lanes": 3, "total": 6},
    "Gate D": {"base_wait": 1,  "lanes": 6, "total": 6},
    "Gate E": {"base_wait": 5,  "lanes": 5, "total": 6},
}
STANDS_CFG = [
    {"id":"s1","name":"Biryani House",  "gate":"B","lvl":1,"wait":2, "items":["Biryani","Raita","Lassi"]},
    {"id":"s2","name":"Burger Co.",     "gate":"C","lvl":2,"wait":18,"items":["Burgers","Fries","Shakes"]},
    {"id":"s3","name":"Chai & Snacks",  "gate":"A","lvl":1,"wait":1, "items":["Chai","Samosa","Vada Pav"]},
    {"id":"s4","name":"Pizza Zone",     "gate":"D","lvl":3,"wait":8, "items":["Pizza","Garlic Bread"]},
    {"id":"s5","name":"Fresh Juice Bar","gate":"E","lvl":1,"wait":3, "items":["Juices","Smoothies"]},
    {"id":"s6","name":"Ice Cream Stand","gate":"A","lvl":2,"wait":7, "items":["Ice Cream","Kulfi"]},
]

def _noise(base, vol):
    global _tick
    _tick += 0.12
    return max(0, min(100, base + math.sin(_tick)*vol*0.5 + random.uniform(-vol*0.3, vol*0.3)))

def _density_level(p):
    return "critical" if p>=80 else "high" if p>=60 else "moderate" if p>=40 else "clear"

def _wait_level(m):
    return "high" if m>=12 else "medium" if m>=6 else "low"

def sensor_crowd():
    zones, total = [], 0
    worst, safest = ("",0), ("",100)
    for name, c in ZONES_CFG.items():
        d = round(_noise(c["base"], c["vol"]), 1)
        count = int(c["cap"]*d/100)
        total += count
        if d > worst[1]:  worst  = (name, d)
        if d < safest[1]: safest = (name, d)
        zones.append({"zone":name,"density_pct":d,"capacity":c["cap"],"current_count":count,
                       "level":_density_level(d),"trend":"stable","last_updated":datetime.now().isoformat()})
    return {"total_occupancy_pct":round(total/STADIUM_CAPACITY*100,1),"total_attendees":total,
            "stadium_capacity":STADIUM_CAPACITY,"zones":zones,
            "hotspot_zone":worst[0],"safest_zone":safest[0],"timestamp":datetime.now().isoformat()}

def sensor_gates():
    gates, best = [], ("",9999)
    for name, c in GATES_CFG.items():
        w = max(1, c["base_wait"] + random.randint(-2,3))
        level = "critical" if w>=12 else "high" if w>=7 else "moderate" if w>=4 else "clear"
        if w < best[1]: best = (name, w)
        gates.append({"gate_id":name.lower().replace(" ","_"),"name":name,"wait_minutes":w,
                       "queue_length":w*random.randint(8,14),"lanes_open":c["lanes"],
                       "lanes_total":c["total"],"congestion":level,
                       "throughput_per_min":random.randint(18,28),"is_recommended":False})
    for g in gates: g["is_recommended"] = (g["name"] == best[0])
    avg = round(sum(g["wait_minutes"] for g in gates)/len(gates), 1)
    return {"gates":gates,"recommended_gate":best[0],"avg_wait_minutes":avg,"timestamp":datetime.now().isoformat()}

def sensor_concessions():
    stands, fastest = [], ("",9999)
    for s in STANDS_CFG:
        w = max(1, s["wait"] + random.randint(-2,4))
        if w < fastest[1]: fastest = (s["name"], w)
        stands.append({"stand_id":s["id"],"name":s["name"],"location":f"Gate {s['gate']} · Level {s['lvl']}",
                        "gate_near":s["gate"],"wait_minutes":w,"wait_level":_wait_level(w),
                        "items_available":s["items"],"is_order_ahead":s["lvl"]==1,
                        "distance_meters":random.randint(40,200)})
    return {"stands":sorted(stands,key=lambda x:x["wait_minutes"]),"fastest_stand":fastest[0],
            "timestamp":datetime.now().isoformat()}

def sensor_alerts():
    return [
        {"alert_id":"a1","title":"Medical team dispatched to Section F","severity":"critical",
         "source":"Ops team","location":"Section F","timestamp":datetime.now().isoformat(),
         "is_ai_generated":False,"action_label":"View on map"},
        {"alert_id":"a2","title":"Gate C reduced to 4 lanes","severity":"warning",
         "source":"Gate ops","location":"Gate C","timestamp":datetime.now().isoformat(),
         "is_ai_generated":False,"action_label":"Redirect via Gate D"},
        {"alert_id":"a3","title":"VIP Box 3 upgrade confirmed","severity":"success",
         "source":"Booking system","location":"VIP Box 3","timestamp":datetime.now().isoformat(),
         "is_ai_generated":False,"action_label":None},
        {"alert_id":"a4","title":"Parking Lot B is full — use Lot D","severity":"info",
         "source":"Parking AI","location":"Lot B","timestamp":datetime.now().isoformat(),
         "is_ai_generated":True,"action_label":"Get directions"},
        {"alert_id":"a5","title":"Biryani House order delivered to Row 14","severity":"success",
         "source":"Concessions","location":"Section B Row 14","timestamp":datetime.now().isoformat(),
         "is_ai_generated":False,"action_label":None},
    ]

def sensor_event():
    return {"event_id":"evt_001","name":"IPL 2026 — Match 38","venue":"Wankhede Stadium, Mumbai",
            "home_team":"Mumbai Indians","away_team":"Chennai Super Kings",
            "home_score":186+random.randint(0,2),"away_score":142,
            "status":"live","period":"47th over","section":"B","row":14,
            "timestamp":datetime.now().isoformat()}


# ═══════════════════════════════════════════════════════════════════
#  AI SERVICE  (Anthropic Claude)
# ═══════════════════════════════════════════════════════════════════

AI_SYSTEM = """You are StadiumIQ — an AI assistant for a smart stadium app.
You have real-time sensor data: crowd density, gate wait times, concession queues, alerts.
Help attendees navigate safely and efficiently. Be concise (under 150 words).
Use bullet points for lists. Give specific, data-grounded answers."""

def _ctx():
    c = sensor_crowd(); g = sensor_gates(); f = sensor_concessions()
    return f"""LIVE STADIUM DATA ({datetime.now().strftime('%H:%M:%S')}):
CROWD: {c['total_occupancy_pct']}% full ({c['total_attendees']:,}/{c['stadium_capacity']:,}) | Hotspot: {c['hotspot_zone']} | Safe: {c['safest_zone']}
ZONES: {' | '.join(f"{z['zone']} {z['density_pct']}% ({z['level']})" for z in c['zones'])}
GATES: Recommend {g['recommended_gate']} | Avg wait {g['avg_wait_minutes']}min | {' | '.join(f"{g2['name']} {g2['wait_minutes']}min" for g2 in g['gates'])}
FOOD (sorted by wait): {' | '.join(f"{s['name']} {s['wait_minutes']}min" for s in f['stands'][:4])}
ALERTS: Gate C reduced lanes · North concourse 80% density · Medical unit at Section F"""

def ai_call(prompt, max_tokens=400):
    if not AI_ENABLED:
        return "AI unavailable — set ANTHROPIC_API_KEY environment variable."
    r = _anthropic_client.messages.create(
        model="claude-opus-4-5", max_tokens=max_tokens,
        system=AI_SYSTEM,
        messages=[{"role":"user","content":prompt}]
    )
    return r.content[0].text

def ai_ask(query, section="B", row=14):
    prompt = f"User: Section {section}, Row {row}\nQuestion: {query}\n\n{_ctx()}"
    answer = ai_call(prompt)
    recs = [l.lstrip("-•* ").strip() for l in answer.split("\n") if l.strip().startswith(("-","•","*"))]
    return {"answer":answer,"recommendations":recs[:5],"confidence":0.92,"timestamp":datetime.now().isoformat()}

def ai_route(frm, to, avoid=True):
    prompt = f"""Give step-by-step walking directions inside Wankhede Stadium.
From: {frm} | To: {to} | Avoid congestion: {avoid}
{_ctx()}
Respond ONLY as JSON: {{"steps":["Step 1..."],"estimated_minutes":5,"congestion_avoided":true}}"""
    raw = ai_call(prompt, 300).replace("```json","").replace("```","").strip()
    try: data = json.loads(raw)
    except: data = {"steps":["Head to nearest stairwell","Follow venue signs","Ask a steward if needed"],"estimated_minutes":5,"congestion_avoided":avoid}
    data["timestamp"] = datetime.now().isoformat()
    return data

def ai_recommendations():
    prompt = f"""Based on live stadium data, generate 3 proactive AI recommendations.
{_ctx()}
Respond ONLY as JSON array: [{{"title":"...","description":"...","severity":"info|warning|critical","action":"..."}}]"""
    raw = ai_call(prompt, 400).replace("```json","").replace("```","").strip()
    try: recs = json.loads(raw)
    except: recs = [
        {"title":"Gate C overloaded — use Gate D","description":"16-min wait at C vs 1-min at D. Redirect now.","severity":"warning","action":"Navigate to Gate D"},
        {"title":"North concourse crowding","description":"82% density. Use East or South routes.","severity":"info","action":"View crowd map"},
        {"title":"Exit wave predicted at full-time","description":"Leave 5 min early via Gate D or A.","severity":"info","action":"Plan early exit"},
    ]
    for i,r in enumerate(recs):
        r.update({"alert_id":f"ai_{i+1:03d}","source":"StadiumIQ AI","timestamp":datetime.now().isoformat(),"is_ai_generated":True})
    return recs

def ai_exit_predict(mins=15):
    prompt = f"""Match ends in {mins} minutes. Predict exit crowd surge and recommend strategy.
{_ctx()}
Respond ONLY as JSON: {{"predicted_surge_minutes":20,"recommended_exit_gates":["Gate D","Gate A"],"strategy":"...","pre_leave_recommendation":true}}"""
    raw = ai_call(prompt, 300).replace("```json","").replace("```","").strip()
    try: data = json.loads(raw)
    except: data = {"predicted_surge_minutes":mins+5,"recommended_exit_gates":["Gate D","Gate A"],
                    "strategy":"Exit via Gate D or A before full-time to avoid the 33k surge. Both gates have <2 min wait right now.",
                    "pre_leave_recommendation":mins<=10}
    data["timestamp"] = datetime.now().isoformat()
    return data


# ═══════════════════════════════════════════════════════════════════
#  REQUEST MODELS
# ═══════════════════════════════════════════════════════════════════

class QueryReq(BaseModel):
    query: str
    user_section: Optional[str] = "B"
    user_row: Optional[int] = 14

class RouteReq(BaseModel):
    from_location: str
    to_location: str
    avoid_congestion: bool = True


# ═══════════════════════════════════════════════════════════════════
#  FASTAPI APP
# ═══════════════════════════════════════════════════════════════════

app = FastAPI(title="StadiumIQ API", version="2.0.0",
              description="AI-powered smart venue management — single file edition")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ── Sensor routes ─────────────────────────────────────────────────

@app.get("/api/crowd")
def crowd(): return sensor_crowd()

@app.get("/api/crowd/{zone}")
def crowd_zone(zone: str):
    d = sensor_crowd()
    z = next((z for z in d["zones"] if z["zone"].lower()==zone.lower()), None)
    if not z: raise HTTPException(404, f"Zone '{zone}' not found")
    return z

@app.get("/api/gates")
def gates(): return sensor_gates()

@app.get("/api/gates/recommended")
def gates_rec():
    d = sensor_gates()
    return {"recommended_gate": next((g for g in d["gates"] if g["is_recommended"]), None), "timestamp": d["timestamp"]}

@app.get("/api/gates/{gate_id}")
def gate(gate_id: str):
    d = sensor_gates()
    g = next((g for g in d["gates"] if g["gate_id"]==gate_id.lower().replace(" ","_")), None)
    if not g: raise HTTPException(404, f"Gate '{gate_id}' not found")
    return g

@app.get("/api/concessions")
def concessions(): return sensor_concessions()

@app.get("/api/concessions/fastest")
def fastest(): d=sensor_concessions(); return {"fastest_stand":d["stands"][0],"timestamp":d["timestamp"]}

@app.get("/api/concessions/by-gate/{gate}")
def by_gate(gate: str):
    d=sensor_concessions()
    return {"stands":[s for s in d["stands"] if s["gate_near"].upper()==gate.upper()],"timestamp":d["timestamp"]}

@app.get("/api/alerts")
def alerts(severity: Optional[str]=None):
    a=sensor_alerts()
    if severity: a=[x for x in a if x["severity"]==severity]
    return {"alerts":a,"count":len(a)}

@app.get("/api/events/live")
def live_event(): return sensor_event()

@app.get("/health")
def health(): return {"status":"ok","ai_enabled":AI_ENABLED,"timestamp":datetime.now().isoformat()}

# ── AI routes ─────────────────────────────────────────────────────

@app.post("/api/ai/ask")
def ask(req: QueryReq):
    if not req.query.strip(): raise HTTPException(400, "Query cannot be empty")
    return ai_ask(req.query, req.user_section, req.user_row)

@app.post("/api/ai/route")
def route(req: RouteReq):
    return ai_route(req.from_location, req.to_location, req.avoid_congestion)

@app.get("/api/ai/recommendations")
def recommendations(): return {"recommendations": ai_recommendations()}

@app.get("/api/ai/predict-exit")
def exit_pred(minutes_to_fulltime: int = Query(15, ge=1, le=120)):
    return ai_exit_predict(minutes_to_fulltime)


# ═══════════════════════════════════════════════════════════════════
#  FRONTEND  (full embedded HTML)
# ═══════════════════════════════════════════════════════════════════

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>StadiumIQ — Smart Venue Experience</title>
<style>
*{box-sizing:border-box;margin:0;padding:0;}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#060c1a;min-height:100vh;display:flex;flex-direction:column;align-items:center;padding:20px 16px 40px;}
h1.page-title{color:rgba(255,255,255,0.18);font-size:11px;letter-spacing:2px;text-transform:uppercase;margin-bottom:16px;font-weight:400;}
.phone{width:390px;background:#0a0f1e;border-radius:40px;overflow:hidden;border:1.5px solid rgba(255,255,255,0.1);}
.status-bar{display:flex;justify-content:space-between;align-items:center;padding:10px 24px 4px;font-size:12px;color:rgba(255,255,255,0.55);}
.topbar{background:#0d1428;border-bottom:0.5px solid rgba(255,255,255,0.08);padding:12px 20px;display:flex;align-items:center;justify-content:space-between;}
.logo{display:flex;align-items:center;gap:8px;}
.logo-icon{width:28px;height:28px;background:#378ADD;border-radius:8px;display:flex;align-items:center;justify-content:center;}
.logo-icon svg{width:16px;height:16px;fill:#fff;}
.logo-text{font-size:16px;font-weight:700;color:#fff;letter-spacing:-0.4px;}
.logo-sub{font-size:10px;color:rgba(255,255,255,0.35);margin-left:2px;}
.live-badge{background:#E24B4A;color:#fff;font-size:10px;font-weight:600;padding:3px 10px;border-radius:20px;display:flex;align-items:center;gap:5px;}
.dot{width:6px;height:6px;border-radius:50%;background:#fff;animation:blink 1.4s infinite;}
@keyframes blink{0%,100%{opacity:1;}50%{opacity:0.3;}}
.nav{display:flex;gap:2px;padding:8px 10px;background:#0d1428;border-bottom:0.5px solid rgba(255,255,255,0.07);}
.nb{flex:1;background:transparent;border:none;color:rgba(255,255,255,0.4);font-size:11px;padding:7px 4px;border-radius:8px;cursor:pointer;font-family:inherit;transition:all .15s;text-align:center;}
.nb.active{background:rgba(55,138,221,0.18);color:#85B7EB;font-weight:600;}
.content{padding:14px;overflow-y:auto;max-height:680px;}
.page{display:none;}.page.shown{display:block;}

/* event card */
.ev-card{background:#0d1428;border:0.5px solid rgba(255,255,255,0.1);border-radius:14px;padding:14px 16px;display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;}
.ev-info h2{font-size:14px;font-weight:600;color:#fff;margin-bottom:3px;}
.ev-info p{font-size:10px;color:rgba(255,255,255,0.38);}
.ev-score{text-align:center;}
.score-num{font-size:24px;font-weight:700;color:#fff;letter-spacing:2px;}
.score-live{font-size:10px;color:#5DCAA5;margin-top:2px;}

/* metrics */
.metrics{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px;margin-bottom:12px;}
.metric{background:#0d1428;border:0.5px solid rgba(255,255,255,0.07);border-radius:12px;padding:10px 8px;}
.ml{font-size:8px;color:rgba(255,255,255,0.38);text-transform:uppercase;letter-spacing:.5px;margin-bottom:4px;}
.mv{font-size:17px;font-weight:700;color:#fff;}
.mv small{font-size:10px;font-weight:400;}
.mc{font-size:8px;margin-top:2px;}
.up{color:#5DCAA5;}.down{color:#E24B4A;}.warn{color:#EF9F27;}

/* panels & gate rows */
.sec{font-size:9px;font-weight:700;color:rgba(255,255,255,0.38);text-transform:uppercase;letter-spacing:.9px;margin-bottom:8px;}
.panel{background:#0d1428;border:0.5px solid rgba(255,255,255,0.07);border-radius:14px;padding:12px;margin-bottom:12px;}
.gate-row{display:flex;align-items:center;gap:8px;padding:8px 0;border-bottom:.5px solid rgba(255,255,255,0.05);}
.gate-row:last-child{border-bottom:none;}
.sdot{width:7px;height:7px;border-radius:50%;flex-shrink:0;}
.sg{background:#1D9E75;}.sa{background:#BA7517;}.sr{background:#E24B4A;}
.glbl{font-size:11px;color:#fff;min-width:48px;}
.btrack{flex:1;height:5px;background:rgba(255,255,255,0.06);border-radius:3px;overflow:hidden;}
.bfill{height:100%;border-radius:3px;transition:width .6s ease;}
.gwait{font-size:10px;font-weight:700;min-width:36px;text-align:right;}

/* alerts */
.alert-list{display:flex;flex-direction:column;gap:8px;margin-bottom:12px;}
.alrt{display:flex;align-items:flex-start;gap:10px;background:#0d1428;border:.5px solid rgba(255,255,255,0.07);border-radius:12px;padding:11px;}
.aico{width:30px;height:30px;border-radius:8px;display:flex;align-items:center;justify-content:center;flex-shrink:0;}
.abu{background:rgba(55,138,221,.14);}.aam{background:rgba(186,117,23,.16);}.agr{background:rgba(29,158,117,.14);}
.abody p{font-size:11px;color:#fff;margin-bottom:2px;line-height:1.4;}
.abody span{font-size:9px;color:rgba(255,255,255,.35);}
.abtn{background:rgba(55,138,221,.14);border:.5px solid rgba(55,138,221,.3);color:#85B7EB;font-size:9px;padding:3px 9px;border-radius:5px;cursor:pointer;margin-top:5px;font-family:inherit;}

/* food */
.food-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;margin-bottom:12px;}
.fc{background:#0d1428;border:.5px solid rgba(255,255,255,0.07);border-radius:12px;padding:11px;}
.fn{font-size:11px;color:#fff;font-weight:500;margin-bottom:3px;}
.fm{font-size:9px;color:rgba(255,255,255,.38);}
.wpill{display:inline-block;font-size:8px;padding:2px 7px;border-radius:20px;margin-top:5px;font-weight:700;}
.wl{background:rgba(29,158,117,.2);color:#5DCAA5;}
.wm{background:rgba(186,117,23,.2);color:#EF9F27;}
.wh{background:rgba(226,75,74,.2);color:#F09595;}

/* map */
.map-wrap{background:#111827;border-radius:12px;overflow:hidden;margin-bottom:12px;}
.legend{display:flex;gap:12px;margin-bottom:8px;}
.li{display:flex;align-items:center;gap:4px;font-size:9px;color:rgba(255,255,255,.45);}
.ld{width:7px;height:7px;border-radius:50%;}

/* notifications */
.nrow{display:flex;align-items:flex-start;gap:10px;padding:9px 0;border-bottom:.5px solid rgba(255,255,255,.05);}
.nrow:last-child{border-bottom:none;}
.nico{width:32px;height:32px;border-radius:8px;display:flex;align-items:center;justify-content:center;flex-shrink:0;}
.ntxt p{font-size:11px;color:#fff;line-height:1.4;}
.ntxt span{font-size:9px;color:rgba(255,255,255,.35);}

/* AI chat panel */
.ai-panel{background:#0d1428;border:.5px solid rgba(55,138,221,.25);border-radius:14px;padding:12px;margin-bottom:12px;}
.ai-title{font-size:9px;font-weight:700;color:#378ADD;text-transform:uppercase;letter-spacing:.7px;margin-bottom:8px;display:flex;align-items:center;gap:5px;}
.ai-chip-row{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:10px;}
.chip{background:rgba(55,138,221,.1);border:.5px solid rgba(55,138,221,.25);color:#85B7EB;font-size:9px;padding:4px 9px;border-radius:20px;cursor:pointer;font-family:inherit;transition:background .15s;}
.chip:hover{background:rgba(55,138,221,.22);}
.ai-input-row{display:flex;gap:6px;}
.ai-input{flex:1;background:rgba(255,255,255,.05);border:.5px solid rgba(255,255,255,.15);border-radius:8px;color:#fff;font-size:11px;padding:7px 10px;font-family:inherit;outline:none;}
.ai-input::placeholder{color:rgba(255,255,255,.3);}
.ai-send{background:#378ADD;border:none;color:#fff;font-size:11px;padding:7px 12px;border-radius:8px;cursor:pointer;font-family:inherit;font-weight:600;white-space:nowrap;}
.ai-send:disabled{opacity:.5;cursor:not-allowed;}
.ai-response{margin-top:10px;background:rgba(55,138,221,.07);border-radius:8px;padding:10px;font-size:11px;color:#c8d8f0;line-height:1.6;display:none;}
.ai-response.shown{display:block;}
.ai-loading{display:none;font-size:10px;color:#378ADD;margin-top:8px;text-align:center;}
.ai-loading.shown{display:block;}

/* primary button */
.pbtn{width:100%;background:#378ADD;border:none;color:#fff;font-size:12px;font-weight:700;padding:13px;border-radius:12px;cursor:pointer;font-family:inherit;margin-bottom:10px;transition:opacity .15s;}
.pbtn:hover{opacity:.88;}.pbtn:active{opacity:.72;}

/* bottom nav */
.bnav{background:#0d1428;border-top:.5px solid rgba(255,255,255,.08);padding:10px 0 20px;display:flex;justify-content:space-around;}
.bi{display:flex;flex-direction:column;align-items:center;gap:3px;cursor:pointer;opacity:.38;transition:opacity .15s;}
.bi.active{opacity:1;}
.bi svg{width:20px;height:20px;fill:none;stroke:#fff;stroke-width:1.5;stroke-linecap:round;stroke-linejoin:round;}
.bi span{font-size:8px;color:#fff;}

/* api status bar */
.api-bar{background:rgba(0,0,0,.4);border-radius:0 0 40px 40px;padding:6px 20px;display:flex;justify-content:space-between;align-items:center;border-top:.5px solid rgba(255,255,255,.04);}
.api-bar span{font-size:9px;color:rgba(255,255,255,.2);}
.api-dot{width:5px;height:5px;border-radius:50%;background:#1D9E75;display:inline-block;margin-right:4px;}
</style>
</head>
<body>

<h1 class="page-title">StadiumIQ · Smart Venue</h1>

<div class="phone">
  <div class="status-bar">
    <span id="clock">9:41</span>
    <span>●●●●&nbsp; WiFi &nbsp;🔋</span>
  </div>

  <div class="topbar">
    <div class="logo">
      <div class="logo-icon">
        <svg viewBox="0 0 16 16"><path d="M8 1L2 4v5c0 3.3 2.5 5.8 6 6.9 3.5-1.1 6-3.6 6-6.9V4L8 1z"/></svg>
      </div>
      <span class="logo-text">StadiumIQ</span>
      <span class="logo-sub">v2.0</span>
    </div>
    <div class="live-badge"><div class="dot"></div>Live</div>
  </div>

  <div class="nav">
    <button class="nb active" onclick="goPage('home',this,0)">Dashboard</button>
    <button class="nb" onclick="goPage('crowd',this,1)">Crowd map</button>
    <button class="nb" onclick="goPage('food',this,2)">Concessions</button>
    <button class="nb" onclick="goPage('alerts',this,3)">Alerts</button>
  </div>

  <div class="content">

    <!-- ── DASHBOARD ── -->
    <div class="page shown" id="page-home">
      <div class="ev-card">
        <div class="ev-info">
          <h2>Mumbai Indians vs CSK</h2>
          <p>Wankhede Stadium · Sec B · Row 14</p>
        </div>
        <div class="ev-score">
          <div class="score-num" id="score-display">186–142</div>
          <div class="score-live">47th over · Live</div>
        </div>
      </div>

      <div class="metrics">
        <div class="metric"><div class="ml">Occupancy</div><div class="mv" id="m-occ">83<small>%</small></div><div class="mc up">+4% avg</div></div>
        <div class="metric"><div class="ml">Avg wait</div><div class="mv" id="m-wait">6<small>m</small></div><div class="mc up">Low today</div></div>
        <div class="metric"><div class="ml">Open gates</div><div class="mv">12</div><div class="mc warn">2 busy</div></div>
        <div class="metric"><div class="ml">Incidents</div><div class="mv">1</div><div class="mc down">Active</div></div>
      </div>

      <div class="sec">Gate status</div>
      <div class="panel" id="gate-panel">
        <div class="gate-row"><div class="sdot sg"></div><div class="glbl">Gate A</div><div class="btrack"><div class="bfill" id="gbar-a" style="width:30%;background:#1D9E75;"></div></div><div class="gwait up" id="gwt-a">2 min</div></div>
        <div class="gate-row"><div class="sdot sa"></div><div class="glbl">Gate B</div><div class="btrack"><div class="bfill" id="gbar-b" style="width:68%;background:#BA7517;"></div></div><div class="gwait warn" id="gwt-b">9 min</div></div>
        <div class="gate-row"><div class="sdot sr"></div><div class="glbl">Gate C</div><div class="btrack"><div class="bfill" id="gbar-c" style="width:91%;background:#E24B4A;"></div></div><div class="gwait down" id="gwt-c">16 min</div></div>
        <div class="gate-row"><div class="sdot sg"></div><div class="glbl">Gate D</div><div class="btrack"><div class="bfill" id="gbar-d" style="width:22%;background:#1D9E75;"></div></div><div class="gwait up" id="gwt-d">1 min</div></div>
        <div class="gate-row"><div class="sdot sg"></div><div class="glbl">Gate E</div><div class="btrack"><div class="bfill" id="gbar-e" style="width:45%;background:#378ADD;"></div></div><div class="gwait" style="color:#85B7EB;" id="gwt-e">5 min</div></div>
      </div>

      <div class="sec">AI recommendations</div>
      <div class="alert-list">
        <div class="alrt"><div class="aico abu"><svg width="14" height="14" viewBox="0 0 16 16" fill="#85B7EB"><path d="M8 1a7 7 0 100 14A7 7 0 008 1zm0 3a1 1 0 011 1v3a1 1 0 01-2 0V5a1 1 0 011-1zm0 7.5a1 1 0 110-2 1 1 0 010 2z"/></svg></div><div class="abody"><p>Gate C overloaded — redirect via Gate D</p><span>AI routing · 2 min ago</span><br><button class="abtn" onclick="askAI('How do I get from Gate C to Gate D quickly?')">Navigate me →</button></div></div>
        <div class="alrt"><div class="aico aam"><svg width="14" height="14" viewBox="0 0 16 16" fill="#EF9F27"><path d="M8 1L1 14h14L8 1zm0 5v4M8 12a.5.5 0 110-1 .5.5 0 010 1z"/></svg></div><div class="abody"><p>North concourse approaching 80% density</p><span>Crowd sensor · 4 min ago</span></div></div>
        <div class="alrt"><div class="aico agr"><svg width="14" height="14" viewBox="0 0 16 16" fill="#5DCAA5"><path d="M8 1a7 7 0 100 14A7 7 0 008 1zm3.5 5l-4 4-2-2 1-1 1 1 3-3 1 1z"/></svg></div><div class="abody"><p>Exit wave predicted at full-time — pre-routing activated</p><span>Predictive AI · Now</span></div></div>
      </div>

      <!-- AI Chat -->
      <div class="sec">Ask StadiumIQ AI</div>
      <div class="ai-panel">
        <div class="ai-title">
          <svg width="12" height="12" viewBox="0 0 16 16" fill="#378ADD"><path d="M8 1a7 7 0 100 14A7 7 0 008 1zm0 3a1 1 0 011 1v3a1 1 0 01-2 0V5a1 1 0 011-1zm0 7.5a1 1 0 110-2 1 1 0 010 2z"/></svg>
          Powered by Claude AI
        </div>
        <div class="ai-chip-row">
          <button class="chip" onclick="askAI('Where is the nearest restroom?')">Nearest restroom</button>
          <button class="chip" onclick="askAI('Which gate has the shortest queue right now?')">Best gate</button>
          <button class="chip" onclick="askAI('What food is available near Section B with short wait?')">Quick food</button>
          <button class="chip" onclick="askAI('How do I exit quickly after the match?')">Exit strategy</button>
        </div>
        <div class="ai-input-row">
          <input class="ai-input" id="ai-q" placeholder="Ask anything about the venue..." onkeydown="if(event.key==='Enter')sendAI()"/>
          <button class="ai-send" id="ai-btn" onclick="sendAI()">Ask →</button>
        </div>
        <div class="ai-loading" id="ai-load">Thinking...</div>
        <div class="ai-response" id="ai-resp"></div>
      </div>

      <button class="pbtn" onclick="askAI('Where is the nearest restroom from Section B Row 14?')">Find nearest restroom →</button>
    </div>

    <!-- ── CROWD MAP ── -->
    <div class="page" id="page-crowd">
      <div class="legend">
        <div class="li"><div class="ld" style="background:#1D9E75;"></div>Clear</div>
        <div class="li"><div class="ld" style="background:#BA7517;"></div>Moderate</div>
        <div class="li"><div class="ld" style="background:#E24B4A;"></div>Congested</div>
      </div>
      <div class="map-wrap">
        <svg viewBox="0 0 340 300" xmlns="http://www.w3.org/2000/svg" style="width:100%;display:block;">
          <rect width="340" height="300" fill="#111827"/>
          <ellipse cx="170" cy="150" rx="130" ry="110" fill="none" stroke="rgba(255,255,255,0.06)" stroke-width="2"/>
          <ellipse cx="170" cy="150" rx="95" ry="78" fill="rgba(29,158,117,0.07)" stroke="rgba(29,158,117,0.22)" stroke-width="1.5"/>
          <rect x="104" y="114" width="132" height="72" rx="8" fill="rgba(55,138,221,0.09)" stroke="rgba(55,138,221,0.2)" stroke-width="1"/>
          <text x="170" y="152" text-anchor="middle" fill="rgba(133,183,235,0.55)" font-size="10" font-family="sans-serif">Playing field</text>
          <!-- North -->
          <rect x="30" y="40" width="62" height="50" rx="7" fill="rgba(226,75,74,0.2)" stroke="#E24B4A" stroke-width="1"/>
          <text x="61" y="66" text-anchor="middle" fill="#F09595" font-size="9" font-weight="bold" font-family="sans-serif">North</text>
          <text x="61" y="79" text-anchor="middle" fill="rgba(240,149,149,0.65)" font-size="8" font-family="sans-serif">88% · Critical</text>
          <!-- East -->
          <rect x="250" y="40" width="62" height="50" rx="7" fill="rgba(29,158,117,0.18)" stroke="#1D9E75" stroke-width="1"/>
          <text x="281" y="66" text-anchor="middle" fill="#5DCAA5" font-size="9" font-weight="bold" font-family="sans-serif">East</text>
          <text x="281" y="79" text-anchor="middle" fill="rgba(93,202,165,0.65)" font-size="8" font-family="sans-serif">34% · Clear</text>
          <!-- West -->
          <rect x="30" y="210" width="62" height="50" rx="7" fill="rgba(186,117,23,0.18)" stroke="#BA7517" stroke-width="1"/>
          <text x="61" y="236" text-anchor="middle" fill="#EF9F27" font-size="9" font-weight="bold" font-family="sans-serif">West</text>
          <text x="61" y="249" text-anchor="middle" fill="rgba(239,159,39,0.65)" font-size="8" font-family="sans-serif">61% · Moderate</text>
          <!-- South -->
          <rect x="250" y="210" width="62" height="50" rx="7" fill="rgba(29,158,117,0.18)" stroke="#1D9E75" stroke-width="1"/>
          <text x="281" y="236" text-anchor="middle" fill="#5DCAA5" font-size="9" font-weight="bold" font-family="sans-serif">South</text>
          <text x="281" y="249" text-anchor="middle" fill="rgba(93,202,165,0.65)" font-size="8" font-family="sans-serif">29% · Clear</text>
          <!-- connectors -->
          <line x1="92" y1="68" x2="108" y2="116" stroke="rgba(226,75,74,0.3)" stroke-width="1" stroke-dasharray="3,3"/>
          <line x1="250" y1="68" x2="236" y2="116" stroke="rgba(29,158,117,0.3)" stroke-width="1" stroke-dasharray="3,3"/>
          <line x1="92" y1="236" x2="108" y2="188" stroke="rgba(186,117,23,0.26)" stroke-width="1" stroke-dasharray="3,3"/>
          <line x1="250" y1="236" x2="236" y2="188" stroke="rgba(29,158,117,0.3)" stroke-width="1" stroke-dasharray="3,3"/>
          <!-- you are here -->
          <circle cx="170" cy="150" r="10" fill="rgba(55,138,221,0.2)"/>
          <circle cx="170" cy="150" r="5" fill="#378ADD"/>
          <text x="170" y="174" text-anchor="middle" fill="rgba(133,183,235,0.7)" font-size="8" font-family="sans-serif">You are here</text>
          <text x="170" y="18" text-anchor="middle" fill="rgba(255,255,255,0.22)" font-size="8" font-family="sans-serif">Real-time crowd density · Wankhede Stadium</text>
        </svg>
      </div>
      <div class="panel">
        <div class="sec" style="margin-bottom:8px;">Zone density</div>
        <div class="gate-row"><div class="sdot sr"></div><div class="glbl">North</div><div class="btrack"><div class="bfill" id="zbar-n" style="width:88%;background:#E24B4A;"></div></div><div class="gwait down" id="zval-n">88%</div></div>
        <div class="gate-row"><div class="sdot sg"></div><div class="glbl">East</div><div class="btrack"><div class="bfill" id="zbar-e" style="width:34%;background:#1D9E75;"></div></div><div class="gwait up" id="zval-e">34%</div></div>
        <div class="gate-row"><div class="sdot sa"></div><div class="glbl">West</div><div class="btrack"><div class="bfill" id="zbar-w" style="width:61%;background:#BA7517;"></div></div><div class="gwait warn" id="zval-w">61%</div></div>
        <div class="gate-row"><div class="sdot sg"></div><div class="glbl">South</div><div class="btrack"><div class="bfill" id="zbar-s" style="width:29%;background:#1D9E75;"></div></div><div class="gwait up" id="zval-s">29%</div></div>
      </div>
      <button class="pbtn" onclick="askAI('Which exit route avoids the North concourse congestion?')">Plan my exit route →</button>
    </div>

    <!-- ── CONCESSIONS ── -->
    <div class="page" id="page-food">
      <div class="sec">Concession stands · near you</div>
      <div class="food-grid" id="food-grid">
        <div class="fc"><div class="fn">Biryani House</div><div class="fm">Gate B · Level 1</div><div class="wpill wl">2 min wait</div></div>
        <div class="fc"><div class="fn">Burger Co.</div><div class="fm">Gate C · Level 2</div><div class="wpill wh">18 min wait</div></div>
        <div class="fc"><div class="fn">Chai &amp; Snacks</div><div class="fm">Gate A · Level 1</div><div class="wpill wl">1 min wait</div></div>
        <div class="fc"><div class="fn">Pizza Zone</div><div class="fm">Gate D · Level 3</div><div class="wpill wm">8 min wait</div></div>
        <div class="fc"><div class="fn">Fresh Juice Bar</div><div class="fm">Gate E · Level 1</div><div class="wpill wl">3 min wait</div></div>
        <div class="fc"><div class="fn">Ice Cream Stand</div><div class="fm">Gate A · Level 2</div><div class="wpill wm">7 min wait</div></div>
      </div>
      <div class="panel">
        <div class="sec" style="margin-bottom:8px;">Order ahead</div>
        <div class="nrow" style="border:none;padding:0;">
          <div class="nico" style="background:rgba(55,138,221,.14);font-size:15px;">🧾</div>
          <div class="ntxt"><p>Skip the queue — pre-order to your seat</p><span>Delivered in 10–15 min</span></div>
        </div>
      </div>
      <button class="pbtn" onclick="askAI('What is the fastest food option near Section B right now?')">Find fastest food →</button>
    </div>

    <!-- ── ALERTS ── -->
    <div class="page" id="page-alerts">
      <div class="sec">Notifications</div>
      <div class="panel">
        <div class="nrow"><div class="nico" style="background:rgba(226,75,74,.14);"><svg width="14" height="14" viewBox="0 0 16 16" fill="#F09595"><path d="M8 1L1 14h14L8 1zm0 4l4.5 8h-9L8 5z"/></svg></div><div class="ntxt"><p>Medical team dispatched to Section F</p><span>Ops team · 1 min ago</span></div></div>
        <div class="nrow"><div class="nico" style="background:rgba(186,117,23,.14);"><svg width="14" height="14" viewBox="0 0 16 16" fill="#EF9F27"><path d="M8 2a6 6 0 100 12A6 6 0 008 2zm0 2v4M8 10.5a.5.5 0 110-1 .5.5 0 010 1z"/></svg></div><div class="ntxt"><p>Gate C reduced to 4 lanes temporarily</p><span>Gate ops · 5 min ago</span></div></div>
        <div class="nrow"><div class="nico" style="background:rgba(29,158,117,.14);"><svg width="14" height="14" viewBox="0 0 16 16" fill="#5DCAA5"><path d="M8 1a7 7 0 100 14A7 7 0 008 1zm3.5 5l-4 4-2-2 1-1 1 1 3-3 1 1z"/></svg></div><div class="ntxt"><p>Your seat upgrade to VIP Box 3 confirmed</p><span>Booking system · 12 min ago</span></div></div>
        <div class="nrow"><div class="nico" style="background:rgba(55,138,221,.14);"><svg width="14" height="14" viewBox="0 0 16 16" fill="#85B7EB"><path d="M8 1a7 7 0 100 14A7 7 0 008 1zm0 3a1 1 0 011 1v3a1 1 0 01-2 0V5a1 1 0 011-1zm0 7.5a1 1 0 110-2 1 1 0 010 2z"/></svg></div><div class="ntxt"><p>Parking Lot B full — use Lot D exit</p><span>Parking AI · 18 min ago</span></div></div>
        <div class="nrow"><div class="nico" style="background:rgba(29,158,117,.14);"><svg width="14" height="14" viewBox="0 0 16 16" fill="#5DCAA5"><path d="M8 1a7 7 0 100 14A7 7 0 008 1zm3.5 5l-4 4-2-2 1-1 1 1 3-3 1 1z"/></svg></div><div class="ntxt"><p>Biryani House order delivered to Row 14</p><span>Concessions · 22 min ago</span></div></div>
      </div>
      <button class="pbtn" onclick="askAI('What are the emergency evacuation procedures for this stadium?')">Emergency info →</button>
    </div>

  </div><!-- end content -->

  <div class="bnav">
    <div class="bi active" onclick="goPage('home',null,0)"><svg viewBox="0 0 24 24"><path d="M3 12L12 3l9 9M5 10v9a1 1 0 001 1h4v-5h4v5h4a1 1 0 001-1v-9"/></svg><span>Home</span></div>
    <div class="bi" onclick="goPage('crowd',null,1)"><svg viewBox="0 0 24 24"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2M9 11a4 4 0 100-8 4 4 0 000 8zM23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75"/></svg><span>Map</span></div>
    <div class="bi" onclick="goPage('food',null,2)"><svg viewBox="0 0 24 24"><path d="M18 8h1a4 4 0 010 8h-1M2 8h16v9a4 4 0 01-4 4H6a4 4 0 01-4-4V8zM6 1v3M10 1v3M14 1v3"/></svg><span>Food</span></div>
    <div class="bi" onclick="goPage('alerts',null,3)"><svg viewBox="0 0 24 24"><path d="M18 8a6 6 0 00-12 0c0 7-3 9-3 9h18s-3-2-3-9M13.73 21a2 2 0 01-3.46 0"/></svg><span>Alerts</span></div>
  </div>

  <div class="api-bar">
    <span><span class="api-dot"></span>API connected · localhost:8000</span>
    <span id="last-refresh">refreshing...</span>
  </div>
</div>

<script>
const BASE = '';

// ── Navigation ─────────────────────────────────────────────────
function goPage(id, btn, idx) {
  document.querySelectorAll('.page').forEach(p=>p.classList.remove('shown'));
  document.getElementById('page-'+id).classList.add('shown');
  document.querySelectorAll('.nb').forEach((b,i)=>b.classList.toggle('active',i===idx));
  document.querySelectorAll('.bi').forEach((b,i)=>b.classList.toggle('active',i===idx));
}

// ── Clock ──────────────────────────────────────────────────────
function updateClock(){
  const now=new Date();
  document.getElementById('clock').textContent=now.getHours()+':'+String(now.getMinutes()).padStart(2,'0');
}
setInterval(updateClock,1000); updateClock();

// ── Live data refresh from API ─────────────────────────────────
const gateCfg = [
  {bar:'gbar-a',wt:'gwt-a',min:10,max:40,color:'#1D9E75'},
  {bar:'gbar-b',wt:'gwt-b',min:55,max:80,color:'#BA7517'},
  {bar:'gbar-c',wt:'gwt-c',min:80,max:98,color:'#E24B4A'},
  {bar:'gbar-d',wt:'gwt-d',min:8, max:30,color:'#1D9E75'},
  {bar:'gbar-e',wt:'gwt-e',min:30,max:60,color:'#378ADD'},
];
const zoneCfg = [
  {bar:'zbar-n',val:'zval-n',min:75,max:95,color:'#E24B4A'},
  {bar:'zbar-e',val:'zval-e',min:25,max:50,color:'#1D9E75'},
  {bar:'zbar-w',val:'zval-w',min:50,max:72,color:'#BA7517'},
  {bar:'zbar-s',val:'zval-s',min:18,max:38,color:'#1D9E75'},
];

async function refreshData(){
  try {
    // Try API first; fall back to simulation
    const [gRes, cRes] = await Promise.all([
      fetch(BASE+'/api/gates').catch(()=>null),
      fetch(BASE+'/api/crowd').catch(()=>null),
    ]);

    if(gRes && gRes.ok){
      const gd = await gRes.json();
      gd.gates.forEach((g,i)=>{
        const cfg=gateCfg[i];
        if(!cfg)return;
        const pct=Math.round(g.wait_minutes/18*100);
        document.getElementById(cfg.bar).style.width=Math.min(pct,100)+'%';
        document.getElementById(cfg.wt).textContent=g.wait_minutes+' min';
      });
    } else {
      // simulate locally
      gateCfg.forEach(c=>{
        const v=Math.round(c.min+Math.random()*(c.max-c.min));
        const wt=Math.round(v/100*18);
        document.getElementById(c.bar).style.width=v+'%';
        document.getElementById(c.wt).textContent=Math.max(1,wt)+' min';
      });
    }

    if(cRes && cRes.ok){
      const cd = await cRes.json();
      document.getElementById('m-occ').innerHTML=Math.round(cd.total_occupancy_pct)+'<small>%</small>';
      cd.zones.forEach(z=>{
        const map={North:'zbar-n',East:'zbar-e',West:'zbar-w',South:'zbar-s'};
        const vmap={North:'zval-n',East:'zval-e',West:'zval-w',South:'zval-s'};
        if(map[z.zone]){
          document.getElementById(map[z.zone]).style.width=z.density_pct+'%';
          document.getElementById(vmap[z.zone]).textContent=Math.round(z.density_pct)+'%';
        }
      });
    } else {
      zoneCfg.forEach(c=>{
        const v=Math.round(c.min+Math.random()*(c.max-c.min));
        document.getElementById(c.bar).style.width=v+'%';
        document.getElementById(c.val).textContent=v+'%';
      });
    }

    document.getElementById('last-refresh').textContent='updated '+new Date().toLocaleTimeString();
  } catch(e){
    document.getElementById('last-refresh').textContent='offline mode';
  }
}

setInterval(refreshData, 4000);
refreshData();

// ── AI Chat ────────────────────────────────────────────────────
async function sendAI(){
  const q=document.getElementById('ai-q').value.trim();
  if(!q)return;
  await askAI(q);
}

async function askAI(query){
  const btn=document.getElementById('ai-btn');
  const inp=document.getElementById('ai-q');
  const load=document.getElementById('ai-load');
  const resp=document.getElementById('ai-resp');

  // scroll to AI panel
  document.getElementById('page-home').scrollIntoView({block:'start'});

  // make sure dashboard is visible
  goPage('home',null,0);

  inp.value=query;
  btn.disabled=true;
  load.classList.add('shown');
  resp.classList.remove('shown');
  resp.textContent='';

  try{
    const res=await fetch(BASE+'/api/ai/ask',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({query,user_section:'B',user_row:14})
    });
    if(res.ok){
      const d=await res.json();
      resp.textContent=d.answer;
    } else {
      resp.textContent='Could not reach AI service. Make sure the Python server is running on port 8000.';
    }
  } catch(e){
    resp.textContent='AI service offline. Start the Python server:\n  python stadiumiq_full.py\n\nMake sure ANTHROPIC_API_KEY is set in your environment.';
  }

  load.classList.remove('shown');
  resp.classList.add('shown');
  btn.disabled=false;
  inp.value='';
}
</script>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
def frontend():
    return HTML


# ═══════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════╗
║              StadiumIQ  v2.0  Starting...               ║
╠══════════════════════════════════════════════════════════╣
║  App   →  http://localhost:8000                         ║
║  Docs  →  http://localhost:8000/docs                    ║
║  AI    →  Set ANTHROPIC_API_KEY env variable            ║
╠══════════════════════════════════════════════════════════╣
║  Install:  pip install fastapi uvicorn anthropic         ║
╚══════════════════════════════════════════════════════════╝
""")
    uvicorn.run("stadiumiq_full:app", host="0.0.0.0", port=8000, reload=True)
