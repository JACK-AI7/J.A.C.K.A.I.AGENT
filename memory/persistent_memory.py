import sqlite3
import os
import json
from datetime import datetime

class PersistentMemory:
    """Long-term memory storage using SQLite with FTS5 for fast text retrieval."""
    
    def __init__(self, db_path="memory/long_term_memory.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Create the main table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    type TEXT,
                    content TEXT,
                    metadata TEXT
                )
            ''')
            # Create FTS5 virtual table for searching
            try:
                cursor.execute('''
                    CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
                        content,
                        content_id UNINDEXED
                    )
                ''')
            except sqlite3.OperationalError:
                # Fallback if FTS5 is not available (though it should be in modern Python)
                print("Warning: FTS5 not supported. Falling back to basic storage.")
            conn.commit()

    def add_memory(self, content, memory_type="chat_summary", metadata=None):
        """Add a new memory to the store."""
        timestamp = datetime.now().isoformat()
        metadata_json = json.dumps(metadata or {})
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO memories (timestamp, type, content, metadata) VALUES (?, ?, ?, ?)",
                (timestamp, memory_type, content, metadata_json)
            )
            memory_id = cursor.lastrowid
            
            # Update FTS index
            try:
                cursor.execute(
                    "INSERT INTO memories_fts (content, content_id) VALUES (?, ?)",
                    (content, memory_id)
                )
            except sqlite3.OperationalError:
                pass
            
            conn.commit()
            return memory_id

    def search(self, query, limit=5):
        """Search memories using keyword matching."""
        results = []
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    SELECT m.content, m.timestamp, m.type, m.metadata
                    FROM memories m
                    JOIN memories_fts f ON m.id = f.content_id
                    WHERE memories_fts MATCH ?
                    ORDER BY rank
                    LIMIT ?
                ''', (query, limit))
                for row in cursor.fetchall():
                    results.append({
                        "content": row[0],
                        "timestamp": row[1],
                        "type": row[2],
                        "metadata": json.loads(row[3])
                    })
            except sqlite3.OperationalError:
                # Basic fallback search
                cursor.execute('''
                    SELECT content, timestamp, type, metadata
                    FROM memories
                    WHERE content LIKE ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (f"%{query}%", limit))
                for row in cursor.fetchall():
                    results.append({
                        "content": row[0],
                        "timestamp": row[1],
                        "type": row[2],
                        "metadata": json.loads(row[3])
                    })
        return results

    def get_recent(self, limit=10):
        """Get the most recent memories."""
        results = []
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT content, timestamp, type, metadata
                FROM memories
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))
            for row in cursor.fetchall():
                results.append({
                    "content": row[0],
                    "timestamp": row[1],
                    "type": row[2],
                    "metadata": json.loads(row[3])
                })
        return results

# Singleton instance
persistent_memory = PersistentMemory()
