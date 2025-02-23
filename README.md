# CitadelDNS

CitadelDNS is an enterprise-grade DNS management system built on top of PowerDNS. It provides a modern REST API for managing DNS records and zones, making it easy to integrate DNS management into your existing infrastructure.

## Features

- Modern REST API for DNS management
- Clean and intuitive React frontend
- Built on PowerDNS for reliability and performance
- Automatic zone creation
- Support for A, AAAA, and TXT records
- CRUD operations (Create, Read, Update, Delete) for all record types
- Direct database integration for better performance
- Simple and intuitive API design
- Modern UI with Mantine components
- Modular and maintainable codebase

## Requirements

- Python 3.8+
- PowerDNS 4.7+
- MariaDB/MySQL
- FastAPI
- uvicorn

## Quick Start

### Automatic Setup

1. Run the setup script as root:
```bash
sudo bash scripts/setup.sh
```

This script will:
- Install all required dependencies (MySQL, PowerDNS, Python, Node.js)
- Configure MySQL with PowerDNS schema
- Set up PowerDNS with API access
- Create systemd services for both backend and frontend
- Build and deploy the frontend
- Start all services

2. Access the application:
- Frontend: http://localhost:56159
- API: http://localhost:53289
- PowerDNS Admin: http://localhost:8081

### Manual Setup

1. Install dependencies:
```bash
# Backend dependencies
pip install -r requirements.txt

# Frontend dependencies
cd frontend
npm install
```

2. Configure PowerDNS with MySQL backend

3. Set up environment variables in `.env`:
```
PDNS_API_KEY=your_api_key
MYSQL_HOST=localhost
MYSQL_USER=pdns
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=powerdns
```

4. Run the applications:
```bash
# Backend
python src/app.py

# Frontend (in another terminal)
cd frontend
npm run dev
```

## API Documentation

The API provides comprehensive CRUD operations for managing DNS records. Here are some examples:

### Create Records

#### Create A Record (IPv4)
```http
POST /api/v1/zones/{zone_name}/records/a
```

Request body:
```json
{
    "name": "www",
    "content": "192.168.1.100",
    "ttl": 3600
}
```

#### Create AAAA Record (IPv6)
```http
POST /api/v1/zones/{zone_name}/records/aaaa
```

Request body:
```json
{
    "name": "www",
    "content": "2001:db8::1",
    "ttl": 3600
}
```

#### Create TXT Record
```http
POST /api/v1/zones/{zone_name}/records/txt
```

Request body:
```json
{
    "name": "verification",
    "content": "google-site-verification=abc123def456",
    "ttl": 3600
}
```

### Modify Records

You can modify any record type using the PUT endpoint:

```http
PUT /api/v1/zones/{zone_name}/records/{record_type}/{record_name}
```

Example (modifying an A record):
```json
{
    "name": "www",
    "content": "192.168.1.200",
    "ttl": 7200
}
```

### Delete Records

To delete a record:

```http
DELETE /api/v1/zones/{zone_name}/records/{record_type}/{record_name}
```

### Response Format

All endpoints return a consistent response format:

Success Response:
```json
{
    "message": "Operation completed successfully"
}
```

Error Response:
```json
{
    "detail": "Error message describing what went wrong"
}
```

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.