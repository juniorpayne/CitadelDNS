#!/bin/bash

# Exit on any error
set -e

echo "Starting CitadelDNS host setup..."

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if a service is active
service_active() {
    systemctl is-active --quiet "$1"
}

# Update package lists
echo "Updating package lists..."
sudo apt-get update

# Install basic requirements
echo "Installing basic requirements..."
sudo apt-get install -y \
    curl \
    gnupg2 \
    software-properties-common \
    apt-transport-https \
    ca-certificates

# Install MySQL if not present
if ! command_exists mysql; then
    echo "Installing MySQL server..."
    sudo apt-get install -y mysql-server
    
    # Start MySQL service
    sudo systemctl start mysql
    sudo systemctl enable mysql
    
    # Reset MySQL root password and secure installation
    echo "Securing MySQL installation..."
    
    # Stop MySQL
    sudo systemctl stop mysql

    # Start MySQL in safe mode
    sudo mysqld_safe --skip-grant-tables --skip-networking &
    sleep 5  # Wait for MySQL to start

    # Reset root password
    echo "Resetting root password..."
    sudo mysql << EOF
FLUSH PRIVILEGES;
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'CitadelDNS123!';
FLUSH PRIVILEGES;
EOF

    # Stop MySQL safe mode
    sudo pkill mysqld
    sleep 5

    # Start MySQL normally
    sudo systemctl start mysql
    sleep 5

    # Secure the installation
    echo "Configuring MySQL security settings..."
    mysql -u root -pCitadelDNS123! << EOF
DELETE FROM mysql.user WHERE User='';
DELETE FROM mysql.user WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1', '::1');
DROP DATABASE IF EXISTS test;
DELETE FROM mysql.db WHERE Db='test' OR Db='test\\_%';
FLUSH PRIVILEGES;

CREATE DATABASE IF NOT EXISTS powerdns;
CREATE USER IF NOT EXISTS 'powerdns'@'localhost' IDENTIFIED BY 'powerdns';
GRANT ALL PRIVILEGES ON powerdns.* TO 'powerdns'@'localhost';
FLUSH PRIVILEGES;
EOF
fi

# Install PowerDNS and its MySQL backend
if ! command_exists pdns_server; then
    echo "Installing PowerDNS and MySQL backend..."
    # Add PowerDNS repository
    curl https://repo.powerdns.com/FD380FBB-pub.asc | sudo apt-key add -
    echo "deb [arch=amd64] http://repo.powerdns.com/ubuntu $(lsb_release -cs)-auth-master main" | \
        sudo tee /etc/apt/sources.list.d/pdns.list
    sudo apt-get update
    
    # Install PowerDNS packages
    sudo apt-get install -y pdns-server pdns-backend-mysql

    # Configure PowerDNS
    echo "Configuring PowerDNS..."
    sudo tee /etc/powerdns/pdns.conf > /dev/null << EOL
launch=gmysql
gmysql-host=localhost
gmysql-user=powerdns
gmysql-password=powerdns
gmysql-dbname=powerdns
api=yes
api-key=CitadelDNS123!
webserver=yes
webserver-address=0.0.0.0
webserver-port=8081
webserver-allow-from=0.0.0.0/0
EOL

    # Import PowerDNS schema
    echo "Importing PowerDNS schema..."
    sudo mysql powerdns < /usr/share/pdns-backend-mysql/schema/schema.mysql.sql

    # Restart PowerDNS
    sudo systemctl restart pdns
    sudo systemctl enable pdns
fi

# Install Python and pip if not present
if ! command_exists python3; then
    echo "Installing Python and pip..."
    sudo apt-get install -y python3 python3-pip python3-venv
fi

# Create Python virtual environment
if [ ! -d "/opt/citadeldns/venv" ]; then
    echo "Creating Python virtual environment..."
    sudo mkdir -p /opt/citadeldns
    sudo python3 -m venv /opt/citadeldns/venv
    sudo chown -R ubuntu:ubuntu /opt/citadeldns
fi

# Install Python dependencies
echo "Installing Python dependencies..."
source /opt/citadeldns/venv/bin/activate
pip install -r requirements.txt

# Verify services are running
echo "Verifying services..."
services=("mysql" "pdns")
for service in "${services[@]}"; do
    if service_active "$service"; then
        echo "$service is running"
    else
        echo "WARNING: $service is not running"
        sudo systemctl start "$service"
    fi
done

echo "Setup complete! Here's what was installed:"
echo "- MySQL Server"
echo "- PowerDNS Server with MySQL backend"
echo "- Python and dependencies"
echo ""
echo "PowerDNS API is available at: http://localhost:8081"
echo "PowerDNS API Key: CitadelDNS123!"
echo "MySQL root password: CitadelDNS123!"
echo ""
echo "Note: Please change these default passwords in a production environment!"