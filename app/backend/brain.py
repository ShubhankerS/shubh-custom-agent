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

    # 1. Physical Data Retrieval via YOUR NASClient
    try:
        client = NASClient()
        pool_data = client.get_pool_status()
        disk_health = client.get_disk_health()
        dataset_quotas = client.get_dataset_quotas()
        service_utilization = client.get_service_utilization()
        
        hardware_state = {
            "pools": pool_data,
            "disks": disk_health,
            "datasets": dataset_quotas,
            "apps": service_utilization
        }
    except Exception as e:
        hardware_state = {"error": f"PHYSICAL_LINK_FAULT: {str(e)}"}

    # 2. Logic Retrieval (RAG)
    docs = get_relevant_docs(user_prompt)
    
    # 3. System Prompt (Your Original Protocol)
    system_context = f"""
    SYSTEM_ROLE: TrueNAS 25.10 Intelligence Engine & Storage Consultant.
    HARDWARE_STATE: {json.dumps(hardware_state)}
    STRATEGY_PREFERENCES: {json.dumps(preferences)}
    MANUAL_LOGIC: {docs}
    
    CONSULTANT_PROTOCOL:
    - Analyze HARDWARE_STATE for unused capacity/performance overhead.
    - If CPU < 20% and RAM > 8GB free, suggest resource-heavy Apps (Nextcloud, Plex, Arr Stack).
    - If Disk Space > 70% utilized, suggest automated cleanup or ZFS compression/deduplication strategies.
    - Proactively mention relevant 'TrueNAS Apps' from the MANUAL_LOGIC when appropriate.
    - Transition to 'Advisory Mode' for long-form strategy discussions, using a more helpful but still technical tone.

    OUTPUT_PROTOCOL:
    - Use Markdown Tables for all status reports.
    - Use code blocks for suggested shell commands.
    - For Advisory/Consultation, use ### ADVISORY header to distinguish from system commands.
    - Zero conversational filler. 
    - If hardware data shows an 'error', diagnose the NAS middleware connectivity first.
    """

    # Assemble Messages with History
    messages = [{"role": "system", "content": system_context}]
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_prompt})

    try:
        response = completion(
            model="gemini/gemini-1.5-flash",
            messages=messages
        )
        answer = response.choices[0].message.content
        
        # 4. Save to Memory
        memory.add_message("user", user_prompt)
        memory.add_message("assistant", answer)
        
        return answer
    except Exception as e: 
        return f"BRAIN_FAULT: {str(e)}"
