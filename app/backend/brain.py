import os
import json
import numpy as np
import litellm
from litellm import completion, embedding
from dotenv import load_dotenv
from pathlib import Path

# Professional Imports
from ..tools.nas_client import NASClient
from .memory_db import AgentMemory

# Path Finder
env_path = Path(__file__).resolve().parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

litellm.api_key = os.getenv("GEMINI_API_KEY")
os.environ["GEMINI_API_VERSION"] = "v1beta"

def get_relevant_docs(user_query, limit=3):
    memory = AgentMemory()
    try:
        query_resp = embedding(model="gemini/gemini-embedding-001", input=[user_query])
        query_vec = np.array(query_resp.data[0]['embedding'])
        with memory.sqlite_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT content, vector FROM knowledge_base")
            rows = cursor.fetchall()
        if not rows: return "DATABASE_EMPTY: Run ingestor to index docs."
        
        scored_chunks = []
        for content, vec_json in rows:
            db_vec = np.array(json.loads(vec_json))
            score = np.dot(query_vec, db_vec)
            scored_chunks.append((score, content))
        
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        return "\n---\n".join([chunk[1] for score, chunk in scored_chunks[:limit]])
    except Exception as e: 
        return f"DOCS_UNAVAILABLE: {str(e)}"

def ask_expert(user_prompt):
    # 0. Load Memory and Preferences
    memory = AgentMemory()
    history = memory.get_history(limit=10)
    preferences = memory.get_preferences()

    # 1. Physical Data Retrieval
    try:
        client = NASClient()
        hardware_state = {
            "pools": client.get_pool_status(),
            "disks": client.get_disk_health(),
            "apps": client.get_service_utilization()
        }
    except Exception:
        hardware_state = {"error": "PHYSICAL_LINK_FAULT"}

    # 2. System Prompt: Human Expert Hardware Advisor
    system_context = f"""
    SYSTEM_ROLE: You are a Human Expert Hardware Advisor for TrueNAS. 
    CHARACTER: Direct, decisive, highly technical. No apologies. No fluff.
    HARDWARE_STATE: {json.dumps(hardware_state)}
    STRATEGY_PREFERENCES: {json.dumps(preferences)}
    
    STRATEGIC_PROTOCOL:
    - If user asks 'what can I do with my NAS?', provide 3 distinct approaches (e.g., Media Center, Backup Node, Home Lab).
    - For each, provide a direct PROS/CONS list based STRICTLY on the HARDWARE_STATE (RAM/CPU/Storage).
    - Proactively identify bottlenecks: If RAM < 16GB, warn about ZFS performance/Apps. If Pool > 80%, warn about fragmentation.
    - If hardware is underutilized (CPU < 10%, high RAM free), suggest specific TrueNAS Apps to maximize ROI.

    OUTPUT_PROTOCOL:
    - Use Markdown Tables for telemetry-heavy reports.
    - Use ### ADVISORY for expert guidance.
    - Use code blocks for ZFS/Shell commands.
    """

    messages = [{"role": "system", "content": system_context}]
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_prompt})

    try:
        response = completion(
            model="gemini/gemini-3-flash-preview",
            messages=messages
        )
        answer = response.choices[0].message.content
        memory.add_message("user", user_prompt)
        memory.add_message("assistant", answer)
        return answer
    except Exception as e:
        return f"BRAIN_FAULT: {str(e)}"
