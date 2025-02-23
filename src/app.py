from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from .api.routes import router
from .config.settings import API_HOST, API_PORT

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

description = """
CitadelDNS API allows you to manage DNS records through a RESTful interface.
It provides endpoints for creating, modifying, and deleting various types of DNS records.

## Features

* Create, modify, and delete A records for IPv4 addresses
* Create, modify, and delete AAAA records for IPv6 addresses
* Create, modify, and delete TXT records for domain verification, SPF records, etc.
* Automatic zone creation if it doesn't exist
* Integration with PowerDNS backend
"""

app = FastAPI(
    title="CitadelDNS Manager API",
    description=description,
    version="1.1.0",
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

app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=API_HOST, port=API_PORT)