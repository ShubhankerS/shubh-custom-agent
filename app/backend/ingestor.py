import os
import json
import time
import litellm
from litellm import embedding
from .memory_db import AgentMemory
from dotenv import load_dotenv

load_dotenv(os.path.join(os.getcwd(), '.env'))
litellm.api_key = os.getenv("GEMINI_API_KEY")

class Ingestor:
    def __init__(self):
        self.memory = AgentMemory()
        self.docs_folder = "docs"

    def process_docs(self):
        if not os.path.exists(self.docs_folder):
            print(f"❌ Error: Folder '{self.docs_folder}' not found.")
            return

        files = [f for f in os.listdir(self.docs_folder) if f.endswith((".md", ".txt"))]
        
        for filename in files:
            file_path = os.path.join(self.docs_folder, filename)
            print(f"📖 Reading: {filename}...")

            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()

            chunks = [text[i:i+1000] for i in range(0, len(text), 1000)]
            
            success_count = 0
            for chunk in chunks:
                retries = 3
                while retries > 0:
                    try:
                        response = embedding(
                            model="gemini/gemini-embedding-001",
                            input=[chunk]
                        )
                        vector_json = json.dumps(response.data[0]['embedding'])
                        self.memory.add_knowledge(chunk, filename, vector_json)
                        
                        success_count += 1
                        # Small delay to stay under the 100 requests/min limit
                        time.sleep(0.6) 
                        break 

                    except Exception as e:
                        if "429" in str(e):
                            print(f"⏳ Rate limit hit. Cooling down for 10 seconds...")
                            time.sleep(10)
                            retries -= 1
                        else:
                            print(f"❌ Error: {e}")
                            retries = 0

            print(f"✅ Successfully taught the agent {success_count} chunks from: {filename}")

if __name__ == "__main__":
    ingestor = Ingestor()
    ingestor.process_docs()