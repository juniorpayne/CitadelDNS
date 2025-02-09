# CitadelDNS

CitadelDNS is an enterprise-grade DNS management system built on top of PowerDNS. It provides a modern REST API for managing DNS records and zones, making it easy to integrate DNS management into your existing infrastructure.

## Features

- Modern REST API for DNS management
- Clean and intuitive React frontend
- Built on PowerDNS for reliability and performance
- Automatic zone creation
- Support for A and TXT records
- Direct database integration for better performance
- Simple and intuitive API design
- Modern UI with Mantine components

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

### Create A Record
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

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.