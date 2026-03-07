import os
import json
import numpy as np
import litellm
from litellm import completion, embedding
from dotenv import load_dotenv
from pathlib import Path
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
        if not rows: return "N/A"
        
        scored_chunks = []
        for content, vec_json in rows:
            db_vec = np.array(json.loads(vec_json))
            score = np.dot(query_vec, db_vec)
            scored_chunks.append((score, content))
        
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        return "\n---\n".join([chunk[1] for score, chunk in scored_chunks[:limit]])
    except: return "DOCS_UNAVAILABLE"

def ask_expert(user_prompt):
    # 1. Physical Data Retrieval
    try:
        client = NASClient()
        pool_data = client.get_pool_status()
    except Exception as e:
        pool_data = {"error": f"ENV_LOAD_FAILURE: {str(e)}"}

    # 2. Logic Retrieval (RAG)
    docs = get_relevant_docs(user_prompt)
    
    # 3. System Prompt (No Pleasantries)
    system_context = f"""
    SYSTEM_ROLE: TrueNAS 25.10 Intelligence Engine.
    HARDWARE_STATE: {json.dumps(pool_data)}
    MANUAL_LOGIC: {docs}
    
    OUTPUT_PROTOCOL:
    - Use Markdown Tables for all status reports.
    - Use code blocks for suggested shell commands.
    - Zero conversational filler. 
    - If hardware data shows an 'error', prioritize diagnosing the connection.
    """

    try:
        response = completion(
            model="gemini/gemini-3-flash-preview",
            messages=[{"role": "system", "content": system_context}, {"role": "user", "content": user_prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"BRAIN_FAULT: {str(e)}"