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

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="pdns",
        password="pdnspass",
        database="powerdns"
    )

@app.post("/api/v1/zones/{zone_name}/records/a")
async def create_a_record(zone_name: str, record: ARecord):
    try:
        if not zone_name.endswith('.'):
            zone_name = zone_name + '.'
            
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
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
        
        cursor.execute("""
            INSERT INTO records (domain_id, name, type, content, ttl)
            VALUES (%s, %s, %s, %s, %s)
        """, (zone_id, record_name, "A", record.content, record.ttl))
        
        conn.commit()
        cursor.close()
        conn.close()

        # Notify PowerDNS of the change
        response = requests.put(
            f"{PDNS_API_URL}/servers/localhost/zones/{zone_name}",
            headers={"X-API-Key": PDNS_API_KEY},
            json={"serial": 0}  # Force serial update
        )

        return {"message": "A record created successfully"}

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)