from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
from typing import Optional
import os
import logging
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="DNS Manager API")

PDNS_API_URL = "http://localhost:8081/api/v1"
PDNS_API_KEY = os.getenv("PDNS_API_KEY", "changeme")

class ARecord(BaseModel):
    name: str
    content: str
    ttl: Optional[int] = 3600

class TXTRecord(BaseModel):
    name: str
    content: str
    ttl: Optional[int] = 3600

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="pdns",
        password="pdnspass",
        database="powerdns"
    )

@app.post("/api/v1/zones/{zone_name}/records/a")
async def create_a_record(zone_name: str, record: ARecord):
    conn = None
    cursor = None
    try:
        if not zone_name.endswith('.'):
            zone_name = zone_name + '.'
            
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            # Check if zone exists
            cursor.execute("SELECT id FROM domains WHERE name = %s", (zone_name,))
            zone = cursor.fetchone()
            
            if not zone:
                # Create zone
                cursor.execute(
                    "INSERT INTO domains (name, type) VALUES (%s, %s)",
                    (zone_name, "NATIVE")
                )
                conn.commit()
                zone_id = cursor.lastrowid
            else:
                zone_id = zone['id']
                
            # Create A record
            record_name = record.name if record.name.endswith(f".{zone_name}") else f"{record.name}.{zone_name}"
            
            cursor.execute(
                "INSERT INTO records (domain_id, name, type, content, ttl) VALUES (%s, %s, %s, %s, %s)",
                (zone_id, record_name, "A", record.content, record.ttl)
            )
            
            conn.commit()

        except mysql.connector.Error as e:
            if conn:
                conn.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

        # Notify PowerDNS of the change
        try:
            response = requests.put(
                f"{PDNS_API_URL}/servers/localhost/zones/{zone_name}",
                headers={"X-API-Key": PDNS_API_KEY},
                json={"serial": 0}  # Force serial update
            )

            if response.status_code >= 400:
                raise HTTPException(
                    status_code=500,
                    detail=f"PowerDNS API error: {response.text}"
                )

        except requests.exceptions.RequestException as e:
            raise HTTPException(status_code=500, detail=f"PowerDNS API error: {str(e)}")

        return {"message": "A record created successfully"}

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.post("/api/v1/zones/{zone_name}/records/txt")
async def create_txt_record(zone_name: str, record: TXTRecord):
    conn = None
    cursor = None
    try:
        if not zone_name.endswith('.'):
            zone_name = zone_name + '.'
            
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            # Check if zone exists
            cursor.execute("SELECT id FROM domains WHERE name = %s", (zone_name,))
            zone = cursor.fetchone()
            
            if not zone:
                # Create zone
                cursor.execute(
                    "INSERT INTO domains (name, type) VALUES (%s, %s)",
                    (zone_name, "NATIVE")
                )
                conn.commit()
                zone_id = cursor.lastrowid
            else:
                zone_id = zone['id']
                
            # Create TXT record
            record_name = record.name if record.name.endswith(f".{zone_name}") else f"{record.name}.{zone_name}"
            
            # Add quotes to content if it contains spaces and isn't already quoted
            content = record.content
            if ' ' in content and not (content.startswith('"') and content.endswith('"')):
                content = f'"{content}"'
            
            cursor.execute(
                "INSERT INTO records (domain_id, name, type, content, ttl) VALUES (%s, %s, %s, %s, %s)",
                (zone_id, record_name, "TXT", content, record.ttl)
            )
            
            conn.commit()

        except mysql.connector.Error as e:
            if conn:
                conn.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

        # Notify PowerDNS of the change
        try:
            response = requests.put(
                f"{PDNS_API_URL}/servers/localhost/zones/{zone_name}",
                headers={"X-API-Key": PDNS_API_KEY},
                json={"serial": 0}  # Force serial update
            )

            if response.status_code >= 400:
                raise HTTPException(
                    status_code=500,
                    detail=f"PowerDNS API error: {response.text}"
                )

        except requests.exceptions.RequestException as e:
            raise HTTPException(status_code=500, detail=f"PowerDNS API error: {str(e)}")

        return {"message": "TXT record created successfully"}

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)