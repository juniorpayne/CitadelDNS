from fastapi import FastAPI, HTTPException, Path
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ConfigDict
import requests
from typing import Optional, Dict, Annotated
import os
import logging
import mysql.connector
from dotenv import load_dotenv
from enum import Enum

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

description = """
CitadelDNS API allows you to manage DNS records through a RESTful interface.
It provides endpoints for creating and managing various types of DNS records.

## Features

* Create A records for IPv4 addresses
* Create TXT records for domain verification, SPF records, etc.
* Automatic zone creation if it doesn't exist
* Integration with PowerDNS backend
"""

app = FastAPI(
    title="CitadelDNS Manager API",
    description=description,
    version="1.0.0",
    contact={
        "name": "CitadelDNS Team",
        "url": "https://github.com/juniorpayne/CitadelDNS",
    },
    license_info={
        "name": "MIT",
    },
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PDNS_API_URL = "http://localhost:8081/api/v1"
PDNS_API_KEY = os.getenv("PDNS_API_KEY", "changeme")

class RecordType(str, Enum):
    A = "A"
    TXT = "TXT"

class DNSRecordBase(BaseModel):
    """Base model for DNS records with common fields."""
    model_config = ConfigDict(json_schema_extra={
        "description": "Base model for DNS records with common fields"
    })

    name: str = Field(
        description="The name of the record relative to the zone (e.g., 'www' for www.example.com)",
        json_schema_extra={"example": "www"}
    )
    ttl: Optional[int] = Field(
        default=3600,
        description="Time To Live in seconds",
        ge=1,
        le=86400,
        json_schema_extra={"example": 3600}
    )

class ARecord(DNSRecordBase):
    """Model for A records that map hostnames to IPv4 addresses."""
    model_config = ConfigDict(json_schema_extra={
        "description": "Model for A records that map hostnames to IPv4 addresses",
        "example": {
            "name": "www",
            "content": "192.168.1.100",
            "ttl": 3600
        }
    })

    content: str = Field(
        description="The IPv4 address",
        pattern=r"^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$",
        json_schema_extra={"example": "192.168.1.100"}
    )

class TXTRecord(DNSRecordBase):
    """Model for TXT records that store text data."""
    model_config = ConfigDict(json_schema_extra={
        "description": "Model for TXT records that store text data",
        "examples": [
            {
                "name": "verification",
                "content": "google-site-verification=abc123def456",
                "ttl": 3600
            },
            {
                "name": "spf",
                "content": "v=spf1 include:_spf.example.com ~all",
                "ttl": 3600
            }
        ]
    })

    content: str = Field(
        description="The text content of the record. Quotes will be added automatically if needed.",
        json_schema_extra={"example": "v=spf1 include:_spf.example.com ~all"}
    )

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="pdns",
        password="pdnspass",
        database="powerdns"
    )

class APIResponse(BaseModel):
    """Standard API response model."""
    message: str = Field(
        description="Response message indicating success or failure",
        min_length=1
    )

class ErrorResponse(BaseModel):
    """Error response model."""
    detail: str = Field(
        description="Detailed error message",
        min_length=1
    )

@app.post(
    "/api/v1/zones/{zone_name}/records/a",
    response_model=APIResponse,
    responses={
        200: {
            "description": "A record created successfully",
            "content": {
                "application/json": {
                    "example": {"message": "A record created successfully"}
                }
            }
        },
        422: {
            "description": "Validation Error",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid IPv4 address format"}
                }
            }
        },
        500: {
            "description": "Internal Server Error",
            "content": {
                "application/json": {
                    "example": {"detail": "Database error: Connection refused"}
                }
            }
        }
    },
    tags=["DNS Records"],
    summary="Create an A record",
    description="Creates a new A record in the specified zone. If the zone doesn't exist, it will be created automatically."
)
async def create_a_record(
    zone_name: Annotated[str, Path(description="The name of the zone (e.g., example.com)", examples=["example.com"])],
    record: ARecord
):
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

@app.post(
    "/api/v1/zones/{zone_name}/records/txt",
    response_model=APIResponse,
    responses={
        200: {
            "description": "TXT record created successfully",
            "content": {
                "application/json": {
                    "example": {"message": "TXT record created successfully"}
                }
            }
        },
        422: {
            "description": "Validation Error",
            "content": {
                "application/json": {
                    "example": {"detail": "Field required: content"}
                }
            }
        },
        500: {
            "description": "Internal Server Error",
            "content": {
                "application/json": {
                    "example": {"detail": "Database error: Connection refused"}
                }
            }
        }
    },
    tags=["DNS Records"],
    summary="Create a TXT record",
    description="""Creates a new TXT record in the specified zone. If the zone doesn't exist, it will be created automatically.
    
    Common uses for TXT records:
    * Domain ownership verification (e.g., for Google Workspace)
    * SPF records for email authentication
    * DKIM records for email signing
    
    The content will be automatically quoted if it contains spaces."""
)
async def create_txt_record(
    zone_name: Annotated[str, Path(description="The name of the zone (e.g., example.com)", examples=["example.com"])],
    record: TXTRecord
):
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
    uvicorn.run(app, host="0.0.0.0", port=53289)