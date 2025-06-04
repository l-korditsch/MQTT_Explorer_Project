import sqlite3
import threading
import json
import os
from datetime import datetime


class MQTTDatabase:
    def __init__(self, db_name="mqtt_messages.db"):
        """Initialize SQLite database"""
        self.db_name = db_name
        self.db_lock = threading.Lock()
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self._init_database()

    def _init_database(self):
        """Create the messages table if it doesn't exist"""
        c = self.conn.cursor()
        c.execute(
            """CREATE TABLE IF NOT EXISTS messages
                    (timestamp TEXT, topic TEXT, message TEXT)"""
        )
        self.conn.commit()

    def save_message(self, timestamp, topic, message):
        """Save message to database"""
        with self.db_lock:
            c = self.conn.cursor()
            c.execute(
                "INSERT INTO messages VALUES (?,?,?)", (timestamp, topic, message)
            )
            self.conn.commit()

    def clear_database(self):
        """Clear the messages database"""
        with self.db_lock:
            c = self.conn.cursor()
            c.execute("DELETE FROM messages")
            self.conn.commit()

    def get_all_messages(self, order_desc=True):
        """Get all messages from database"""
        with self.db_lock:
            c = self.conn.cursor()
            order = "DESC" if order_desc else "ASC"
            c.execute(f"SELECT * FROM messages ORDER BY timestamp {order}")
            return c.fetchall()

    def get_recent_messages(self, limit=10):
        """Get recent messages from database"""
        with self.db_lock:
            c = self.conn.cursor()
            c.execute(
                "SELECT * FROM messages ORDER BY timestamp DESC LIMIT ?", (limit,)
            )
            return c.fetchall()

    def export_to_json(self, filepath=None):
        """Export database contents to a JSON file"""
        try:
            rows = self.get_all_messages(order_desc=False)

            # Create export data
            export_data = []
            for row in rows:
                export_data.append(
                    {"timestamp": row[0], "topic": row[1], "message": row[2]}
                )

            # Generate filename if not provided
            if not filepath:
                filename = (
                    f"mqtt_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                )
                filepath = os.path.join("./Storage/", filename)

            # Ensure directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            with open(filepath, "w") as f:
                json.dump(export_data, f, indent=2)

            return filepath

        except Exception as e:
            raise Exception(f"Failed to export database: {e}")

    def close(self):
        """Close database connection"""
        if hasattr(self, "conn"):
            self.conn.close()

    def __del__(self):
        """Cleanup on exit"""
        self.close()
