from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .brain import ask_expert
from .memory_db import AgentMemory

app = FastAPI(title="shubh-custom-agent API")

# Security: Allow the frontend to talk to the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allows any local file to talk to the API
    allow_methods=["*"],
    allow_headers=["*"],
)

memory = AgentMemory()

class Question(BaseModel):
    prompt: str

@app.get("/")
def health_check():
    return {"status": "Online", "agent": "shubh-custom-agent"}

@app.post("/ask")
def chat(query: Question):
    response = ask_expert(query.prompt)
    memory.add_message("user", query.prompt)
    memory.add_message("assistant", response)
    return {"answer": response}

@app.get("/history")
def get_history():
    return memory.get_history()