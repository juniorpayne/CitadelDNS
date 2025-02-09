#!/bin/bash

# Exit on error
set -e

# Function to print messages
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if script is run as root
if [ "$EUID" -ne 0 ]; then
    log "Please run this script as root"
    exit 1
fi

# Install dependencies
log "Installing dependencies..."
apt-get update
apt-get install -y \
    default-mysql-server \
    pdns-server \
    pdns-backend-mysql \
    python3 \
    python3-pip \
    nodejs \
    npm

# Configure MySQL
log "Configuring MySQL..."
MYSQL_ROOT_PASSWORD=$(openssl rand -hex 16)
PDNS_DB_PASSWORD=$(openssl rand -hex 16)

# Start MySQL service
service mariadb start || service mysql start

# Wait for MySQL to be ready
for i in {1..30}; do
    if mysqladmin ping &>/dev/null; then
        break
    fi
    log "Waiting for MySQL to start..."
    sleep 1
done

# Secure MySQL installation
mysql -e "SET PASSWORD FOR 'root'@'localhost' = PASSWORD('${MYSQL_ROOT_PASSWORD}');"
mysql -e "DELETE FROM mysql.user WHERE User='';"
mysql -e "DELETE FROM mysql.user WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1', '::1');"
mysql -e "DROP DATABASE IF EXISTS test;"
mysql -e "DELETE FROM mysql.db WHERE Db='test' OR Db='test\\_%';"
mysql -e "FLUSH PRIVILEGES;"

# Create PowerDNS database and user
mysql -u root <<EOF
CREATE DATABASE IF NOT EXISTS powerdns;
CREATE USER IF NOT EXISTS 'pdns'@'localhost' IDENTIFIED BY '${PDNS_DB_PASSWORD}';
GRANT ALL PRIVILEGES ON powerdns.* TO 'pdns'@'localhost';
FLUSH PRIVILEGES;
EOF

# Import PowerDNS schema (ignore errors if tables already exist)
mysql -u root powerdns < /usr/share/pdns-backend-mysql/schema/schema.mysql.sql 2>/dev/null || true

# Configure PowerDNS
log "Configuring PowerDNS..."
cat > /etc/powerdns/pdns.conf <<EOF
api=yes
api-key=${PDNS_API_KEY:-changeme}
webserver=yes
webserver-address=0.0.0.0
webserver-port=8081
webserver-allow-from=0.0.0.0/0
launch=gmysql
gmysql-host=localhost
gmysql-user=pdns
gmysql-password=${PDNS_DB_PASSWORD}
gmysql-dbname=powerdns
EOF

# Create environment file
log "Creating environment file..."
cat > /workspace/CitadelDNS/.env <<EOF
PDNS_API_KEY=${PDNS_API_KEY:-changeme}
MYSQL_HOST=localhost
MYSQL_USER=pdns
MYSQL_PASSWORD=${PDNS_DB_PASSWORD}
MYSQL_DATABASE=powerdns
EOF

# Install Python dependencies
log "Installing Python dependencies..."
cd /workspace/CitadelDNS
pip3 install -r requirements.txt

# Create systemd service for CitadelDNS
log "Creating systemd service..."
cat > /etc/systemd/system/citadeldns.service <<EOF
[Unit]
Description=CitadelDNS Manager
After=network.target mysql.service pdns.service

[Service]
Type=simple
User=root
WorkingDirectory=/workspace/CitadelDNS
Environment=PYTHONPATH=/workspace/CitadelDNS
ExecStart=/usr/bin/python3 src/app.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Create systemd service for frontend
log "Creating systemd service for frontend..."
cat > /etc/systemd/system/citadeldns-frontend.service <<EOF
[Unit]
Description=CitadelDNS Frontend
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/workspace/CitadelDNS/frontend
Environment=NODE_ENV=production
ExecStart=/usr/bin/npm run preview
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Build frontend
log "Building frontend..."
cd /workspace/CitadelDNS/frontend
npm install
npm run build

# Start services
log "Starting services..."
service mariadb start || service mysql start
/usr/sbin/pdns_server --daemon=no --guardian=no --config-dir=/etc/powerdns > pdns.log 2>&1 &
cd /workspace/CitadelDNS && python3 src/app.py > backend.log 2>&1 &
cd /workspace/CitadelDNS/frontend && npm run preview > frontend.log 2>&1 &

# Wait for services to start
sleep 5

# Check service status
log "Service status:"
ps aux | grep -E "pdns_server|app.py|npm" | grep -v grep

# Print setup information
log "Setup completed successfully!"
log "MySQL root password: ${MYSQL_ROOT_PASSWORD}"
log "PowerDNS API key: ${PDNS_API_KEY:-changeme}"
log "PowerDNS Admin Interface: http://localhost:8081"
log "CitadelDNS API: http://localhost:53289"
log "CitadelDNS Frontend: http://localhost:56159"