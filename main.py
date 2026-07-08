"""
StadiumIQ Backend — AI-powered smart venue experience
FastAPI + Anthropic Claude + simulated IoT sensor data
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn

from routes.crowd import router as crowd_router
from routes.gates import router as gates_router
from routes.concessions import router as concessions_router
from routes.alerts import router as alerts_router
from routes.ai import router as ai_router
from routes.events import router as events_router

app = FastAPI(
    title="StadiumIQ API",
    description="AI-powered smart venue management backend",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(crowd_router,       prefix="/api/crowd",       tags=["Crowd"])
app.include_router(gates_router,       prefix="/api/gates",       tags=["Gates"])
app.include_router(concessions_router, prefix="/api/concessions", tags=["Concessions"])
app.include_router(alerts_router,      prefix="/api/alerts",      tags=["Alerts"])
app.include_router(ai_router,          prefix="/api/ai",          tags=["AI"])
app.include_router(events_router,      prefix="/api/events",      tags=["Events"])

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", include_in_schema=False)
def root():
    return FileResponse("static/index.html")

@app.get("/health")
def health():
    return {"status": "ok", "service": "StadiumIQ API v2.0"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
