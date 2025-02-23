from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from enum import Enum

class RecordType(str, Enum):
    A = "A"
    AAAA = "AAAA"
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

class AAAARecord(DNSRecordBase):
    """Model for AAAA records that map hostnames to IPv6 addresses."""
    model_config = ConfigDict(json_schema_extra={
        "description": "Model for AAAA records that map hostnames to IPv6 addresses",
        "example": {
            "name": "www",
            "content": "2001:db8::1",
            "ttl": 3600
        }
    })

    content: str = Field(
        description="The IPv6 address",
        pattern=r"^(?:[A-F0-9]{1,4}:){7}[A-F0-9]{1,4}$|^(?:[A-F0-9]{1,4}:){6}:[A-F0-9]{1,4}$|^(?:[A-F0-9]{1,4}:){5}(?::[A-F0-9]{1,4}){1,2}$|^(?:[A-F0-9]{1,4}:){4}(?::[A-F0-9]{1,4}){1,3}$|^(?:[A-F0-9]{1,4}:){3}(?::[A-F0-9]{1,4}){1,4}$|^(?:[A-F0-9]{1,4}:){2}(?::[A-F0-9]{1,4}){1,5}$|^[A-F0-9]{1,4}:(?::[A-F0-9]{1,4}){1,6}$|^:(?::[A-F0-9]{1,4}){1,7}$|^::$",
        json_schema_extra={"example": "2001:db8::1"}
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