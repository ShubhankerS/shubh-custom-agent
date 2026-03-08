import sqlite3
import os

class AgentMemory:
    def __init__(self, db_path="data/agent_memory.db"):
        self.db_path = db_path
        # Ensures the 'data' folder exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_db()

    def sqlite_connection(self):
        """Helper to provide a connection for the search function in brain.py."""
        return sqlite3.connect(self.db_path)

    def init_db(self):
        """Sets up the tables for chat history and the knowledge base."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Table 1: Chat History (Conversation memory)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    role TEXT,
                    content TEXT
                )
            """)
            
            # Table 2: Knowledge Base (RAG memory for your docs)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_base (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT,        -- The actual text from your .md files
                    source TEXT,         -- The filename (e.g., 'goldeye_manual.md')
                    vector BLOB          -- The 'Secret Code' numbers (JSON string)
                )
            """)

            # Table 3: User Preferences (Long-term Strategy Memory)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_preferences (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def add_message(self, role, content):
        """Saves a conversation message."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO chat_history (role, content) VALUES (?, ?)", (role, content))
            conn.commit()

    def set_preference(self, key, value):
        """Stores or updates a user preference."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO user_preferences (key, value) VALUES (?, ?)", (key, value))
            conn.commit()

    def get_preferences(self):
        """Retrieves all user preferences."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT key, value FROM user_preferences")
            return {row[0]: row[1] for row in cursor.fetchall()}

    def get_history(self, limit=20):
        """Retrieves conversation history."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT role, content FROM chat_history ORDER BY timestamp ASC LIMIT ?", (limit,))
            return [{"role": row[0], "content": row[1]} for row in cursor.fetchall()]

    def add_knowledge(self, content, source, vector_data):
        """Saves a chunk of documentation and its vector code."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO knowledge_base (content, source, vector) VALUES (?, ?, ?)",
                (content, source, vector_data)
            )
            conn.commit()