# StadiumIQ — AI-Powered Smart Venue Backend

> Hackathon-ready Python backend for the StadiumIQ smart stadium experience app.
> Built with FastAPI + Anthropic Claude + simulated IoT sensor data.

---

## Architecture

```
stadiumiq/
├── main.py                  # FastAPI app, CORS, route registration
├── requirements.txt
├── .env.example
├── models/
│   └── __init__.py          # Pydantic schemas for all data types
├── services/
│   ├── sensor_sim.py        # Simulated IoT crowd/gate/food sensor data
│   └── ai_service.py        # Anthropic Claude integration (AI brain)
├── routes/
│   ├── crowd.py             # GET /api/crowd/*
│   ├── gates.py             # GET /api/gates/*
│   ├── concessions.py       # GET /api/concessions/*
│   ├── alerts.py            # GET /api/alerts/*
│   ├── events.py            # GET /api/events/*
│   └── ai.py                # POST /api/ai/* (Claude-powered)
└── static/
    └── index.html           # Frontend (StadiumIQ app)
```

---

## Quick Start

### 1. Clone and install

```bash
cd stadiumiq
pip install -r requirements.txt
```

### 2. Set your API key

```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### 3. Run

```bash
python main.py
# or
uvicorn main:app --reload --port 8000
```

### 4. Open

- App: http://localhost:8000
- API Docs (Swagger): http://localhost:8000/docs
- API Docs (Redoc): http://localhost:8000/redoc

---

## API Endpoints

### Sensor Data (live simulated IoT)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/crowd` | All zone crowd densities |
| GET | `/api/crowd/{zone}` | Single zone (North/East/West/South) |
| GET | `/api/gates` | All gate wait times |
| GET | `/api/gates/recommended` | Least congested gate |
| GET | `/api/gates/{gate_id}` | Single gate status |
| GET | `/api/concessions` | All concession stands with queues |
| GET | `/api/concessions/fastest` | Lowest wait stand |
| GET | `/api/concessions/by-gate/{gate}` | Stands near a gate |
| GET | `/api/alerts` | All active alerts |
| GET | `/api/alerts/critical` | Critical alerts only |
| GET | `/api/events/live` | Live match score and info |

### AI Endpoints (Claude-powered)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/ai/ask` | Natural language Q&A with live context |
| POST | `/api/ai/route` | Step-by-step in-venue navigation |
| GET | `/api/ai/recommendations` | Proactive AI alerts |
| GET | `/api/ai/predict-exit` | Exit wave prediction |

---

## Example AI Requests

### Ask a question
```bash
curl -X POST http://localhost:8000/api/ai/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "Which gate should I use to avoid the crowd?", "user_section": "B", "user_row": 14}'
```

### Get a route
```bash
curl -X POST http://localhost:8000/api/ai/route \
  -H "Content-Type: application/json" \
  -d '{"from_location": "Section B Row 14", "to_location": "Gate D", "avoid_congestion": true}'
```

### Predict exit wave
```bash
curl "http://localhost:8000/api/ai/predict-exit?minutes_to_fulltime=10"
```

---

## How the AI Works

Every AI endpoint builds a **live context snapshot** from the sensor simulation layer, then sends it to Claude along with the user's query. Claude reasons over real-time data to give answers grounded in the actual stadium state — not generic advice.

```
User query
    ↓
sensor_sim.py  →  live crowd + gate + food data
    ↓
ai_service.py  →  builds context string + calls Claude
    ↓
Claude (claude-opus-4-5)  →  generates grounded response
    ↓
API response with answer + recommendations
```

---

## Production Upgrade Path

| Demo (now) | Production |
|---|---|
| `sensor_sim.py` (fake data) | BLE/Wi-Fi triangulation sensors |
| In-memory state | Redis / TimescaleDB |
| Single process | Kubernetes + WebSockets |
| Simulated alerts | PagerDuty / Ops integration |
| Static frontend | React Native mobile app |

---

## Hackathon Pitch Points

- **Real-time AI routing** — Claude re-calculates optimal paths every 60s using live sensor data
- **Predictive crowd management** — exit wave modelling 15-20min before full-time
- **Zero-queue concessions** — AI surfaces lowest-wait stands and enables pre-ordering
- **Natural language interface** — attendees ask questions in plain English, AI answers with venue context
- **Ops dashboard** — same API powers both attendee app and staff management console
