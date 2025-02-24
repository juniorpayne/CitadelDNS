import mysql.connector
from mysql.connector.cursor import MySQLCursor
from typing import Optional, Dict, Any
from ..config.settings import DB_CONFIG

class DatabaseManager:
    def __init__(self):
        self.config = DB_CONFIG

    def get_connection(self):
        return mysql.connector.connect(**self.config)

    def ensure_zone_exists(self, cursor: MySQLCursor, zone_name: str) -> int:
        """Ensure zone exists and return its ID."""
        cursor.execute("SELECT id FROM domains WHERE name = %s", (zone_name,))
        zone = cursor.fetchone()
        
        if not zone:
            cursor.execute(
                "INSERT INTO domains (name, type) VALUES (%s, %s)",
                (zone_name, "NATIVE")
            )
            cursor.connection.commit()
            return cursor.lastrowid
        return zone['id']

    def create_record(self, zone_name: str, record_name: str, record_type: str, 
                     content: str, ttl: int) -> None:
        """Create a new DNS record."""
        conn = None
        cursor = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            zone_id = self.ensure_zone_exists(cursor, zone_name)
            
            # Add quotes to TXT record content if needed
            if record_type == "TXT" and ' ' in content and not (content.startswith('"') and content.endswith('"')):
                content = f'"{content}"'
            
            cursor.execute(
                "INSERT INTO records (domain_id, name, type, content, ttl) VALUES (%s, %s, %s, %s, %s)",
                (zone_id, record_name, record_type, content, ttl)
            )
            
            conn.commit()
            
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def modify_record(self, zone_name: str, record_name: str, record_type: str,
                     new_content: str, new_ttl: Optional[int] = None) -> bool:
        """Modify an existing DNS record."""
        conn = None
        cursor = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            if new_ttl is not None:
                cursor.execute(
                    "UPDATE records r JOIN domains d ON r.domain_id = d.id SET r.content = %s, r.ttl = %s WHERE d.name = %s AND r.name = %s AND r.type = %s",
                    (new_content, new_ttl, zone_name, record_name, record_type)
                )
            else:
                cursor.execute(
                    "UPDATE records r JOIN domains d ON r.domain_id = d.id SET r.content = %s WHERE d.name = %s AND r.name = %s AND r.type = %s",
                    (new_content, zone_name, record_name, record_type)
                )
            
            conn.commit()
            return cursor.rowcount > 0
            
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def delete_record(self, zone_name: str, record_name: str, record_type: str) -> bool:
        """Delete a DNS record."""
        conn = None
        cursor = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute(
                "DELETE r FROM records r JOIN domains d ON r.domain_id = d.id WHERE d.name = %s AND r.name = %s AND r.type = %s",
                (zone_name, record_name, record_type)
            )
            
            conn.commit()
            return cursor.rowcount > 0
            
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def get_record(self, zone_name: str, record_name: str, record_type: str) -> Optional[Dict[str, Any]]:
        """Get a DNS record."""
        conn = None
        cursor = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute(
                "SELECT r.* FROM records r JOIN domains d ON r.domain_id = d.id WHERE d.name = %s AND r.name = %s AND r.type = %s",
                (zone_name, record_name, record_type)
            )
            
            return cursor.fetchone()
            
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()