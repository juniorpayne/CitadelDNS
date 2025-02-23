from fastapi import APIRouter, HTTPException, Path
from typing import Annotated
from ..models.dns_records import ARecord, AAAARecord, TXTRecord, APIResponse
from ..database.db_operations import DatabaseManager
from ..api.pdns_api import PowerDNSAPI

router = APIRouter(prefix="/api/v1")
db = DatabaseManager()
pdns = PowerDNSAPI()

def normalize_zone_name(zone_name: str) -> str:
    """Ensure zone name ends with a dot."""
    return zone_name if zone_name.endswith('.') else zone_name + '.'

def normalize_record_name(record_name: str, zone_name: str) -> str:
    """Ensure record name is fully qualified."""
    return record_name if record_name.endswith(f".{zone_name}") else f"{record_name}.{zone_name}"

@router.post(
    "/zones/{zone_name}/records/a",
    response_model=APIResponse,
    tags=["DNS Records"],
    summary="Create an A record",
    description="Creates a new A record in the specified zone. If the zone doesn't exist, it will be created automatically."
)
async def create_a_record(
    zone_name: Annotated[str, Path(description="The name of the zone (e.g., example.com)")],
    record: ARecord
):
    zone_name = normalize_zone_name(zone_name)
    record_name = normalize_record_name(record.name, zone_name)
    
    try:
        db.create_record(zone_name, record_name, "A", record.content, record.ttl)
        pdns.notify_zone_change(zone_name)
        return {"message": "A record created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/zones/{zone_name}/records/aaaa",
    response_model=APIResponse,
    tags=["DNS Records"],
    summary="Create an AAAA record",
    description="Creates a new AAAA record in the specified zone. If the zone doesn't exist, it will be created automatically."
)
async def create_aaaa_record(
    zone_name: Annotated[str, Path(description="The name of the zone (e.g., example.com)")],
    record: AAAARecord
):
    zone_name = normalize_zone_name(zone_name)
    record_name = normalize_record_name(record.name, zone_name)
    
    try:
        db.create_record(zone_name, record_name, "AAAA", record.content, record.ttl)
        pdns.notify_zone_change(zone_name)
        return {"message": "AAAA record created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/zones/{zone_name}/records/txt",
    response_model=APIResponse,
    tags=["DNS Records"],
    summary="Create a TXT record",
    description="Creates a new TXT record in the specified zone. If the zone doesn't exist, it will be created automatically."
)
async def create_txt_record(
    zone_name: Annotated[str, Path(description="The name of the zone (e.g., example.com)")],
    record: TXTRecord
):
    zone_name = normalize_zone_name(zone_name)
    record_name = normalize_record_name(record.name, zone_name)
    
    try:
        db.create_record(zone_name, record_name, "TXT", record.content, record.ttl)
        pdns.notify_zone_change(zone_name)
        return {"message": "TXT record created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put(
    "/zones/{zone_name}/records/{record_type}/{record_name}",
    response_model=APIResponse,
    tags=["DNS Records"],
    summary="Modify a DNS record",
    description="Modifies an existing DNS record of the specified type."
)
async def modify_record(
    zone_name: Annotated[str, Path(description="The name of the zone (e.g., example.com)")],
    record_type: Annotated[str, Path(description="The type of record (A, AAAA, or TXT)")],
    record_name: Annotated[str, Path(description="The name of the record")],
    record: ARecord | AAAARecord | TXTRecord
):
    zone_name = normalize_zone_name(zone_name)
    record_name = normalize_record_name(record_name, zone_name)
    
    try:
        if not db.modify_record(zone_name, record_name, record_type, record.content, record.ttl):
            raise HTTPException(status_code=404, detail="Record not found")
        
        pdns.notify_zone_change(zone_name)
        return {"message": f"{record_type} record modified successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete(
    "/zones/{zone_name}/records/{record_type}/{record_name}",
    response_model=APIResponse,
    tags=["DNS Records"],
    summary="Delete a DNS record",
    description="Deletes an existing DNS record of the specified type."
)
async def delete_record(
    zone_name: Annotated[str, Path(description="The name of the zone (e.g., example.com)")],
    record_type: Annotated[str, Path(description="The type of record (A, AAAA, or TXT)")],
    record_name: Annotated[str, Path(description="The name of the record")]
):
    zone_name = normalize_zone_name(zone_name)
    record_name = normalize_record_name(record_name, zone_name)
    
    try:
        if not db.delete_record(zone_name, record_name, record_type):
            raise HTTPException(status_code=404, detail="Record not found")
        
        pdns.notify_zone_change(zone_name)
        return {"message": f"{record_type} record deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))