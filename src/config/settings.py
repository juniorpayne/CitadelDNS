from dotenv import load_dotenv
import os

load_dotenv()

PDNS_API_URL = "http://localhost:8081/api/v1"
PDNS_API_KEY = os.getenv("PDNS_API_KEY", "changeme")

DB_CONFIG = {
    "host": "localhost",
    "user": "pdns",
    "password": "pdnspass",
    "database": "powerdns"
}

API_PORT = 51095  # Using the provided port
API_HOST = "0.0.0.0"