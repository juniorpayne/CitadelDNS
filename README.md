# CitadelDNS

CitadelDNS is an enterprise-grade DNS management system built on top of PowerDNS. It provides a modern REST API for managing DNS records and zones, making it easy to integrate DNS management into your existing infrastructure.

## Features

- Modern REST API for DNS management
- Built on PowerDNS for reliability and performance
- Automatic zone creation
- Support for A records (more record types coming soon)
- Direct database integration for better performance
- Simple and intuitive API design

## Requirements

- Python 3.8+
- PowerDNS 4.7+
- MariaDB/MySQL
- FastAPI
- uvicorn

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure PowerDNS with MySQL backend

3. Set up environment variables in `.env`:
```
PDNS_API_KEY=your_api_key
```

4. Run the application:
```bash
python src/app.py
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