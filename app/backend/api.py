import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# These are YOUR original modules - we keep these!
from .brain import ask_expert
from .memory_db import AgentMemory

app = FastAPI(title="shubh-custom-agent API")

# Security: Your original CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

memory = AgentMemory()

class Question(BaseModel):
    prompt: str

# --- NEW: FRONTEND SERVING (The fix for the JSON screen) ---
# This points to the folder where your index.html lives
FRONTEND_DIR = "/app/app/frontend"

# Serve static assets (CSS/JS)
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

# The Root Route: Instead of returning JSON, it returns your Console
@app.get("/", response_class=HTMLResponse)
def serve_ui():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return "<h1>System Error: Frontend not found at /app/app/frontend/index.html</h1>"
# ---------------------------------------------------------

@app.get("/health")
def health_check():
    return {"status": "Online", "agent": "shubh-custom-agent"}

@app.post("/ask")
def chat(query: Question):
    # This calls your brain.py logic (RAG, Gemini, etc.)
    response = ask_expert(query.prompt)
    memory.add_message("user", query.prompt)
    memory.add_message("assistant", response)
    return {"answer": response}

@app.get("/history")
def get_history():
    return memory.get_history()

# --- NEW: Real-time Telemetry Endpoint ---
from ..tools.nas_client import NASClient

@app.get("/telemetry")
def get_telemetry():
    """Independent telemetry route for the UI sidebar."""
    client = NASClient()
    return client.get_telemetry()
# -----------------------------------------
