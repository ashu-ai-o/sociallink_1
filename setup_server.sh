#!/bin/bash

# ==============================================================================
# SOCIAL LINK - SERVER SETUP SCRIPT (DigitalOcean Droplet)
# ==============================================================================
# This script installs Docker, Docker Compose, and sets up the environment.
# Run this as root: sudo bash setup_server.sh
# ==============================================================================

set -e

echo "🚀 Starting server setup..."

# 1. Update system
apt-get update && apt-get upgrade -y

# 2. Install Docker
echo "📦 Installing Docker..."
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
rm get-docker.sh

# 3. Enable Docker on boot
systemctl enable docker
systemctl start docker

# 4. Install Docker Compose
echo "📦 Installing Docker Compose..."
DOCKER_COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep -Po '"tag_name": "\K.*?(?=")')
curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# 5. Setup Firewall (UFW)
echo "🛡️ Setting up Firewall..."
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 8000/tcp
echo "y" | ufw enable

# 6. Create Application Directory
mkdir -p /var/www/sociallink
chown -R $USER:$USER /var/www/sociallink

echo "✅ Setup complete! You can now deploy your docker-compose.prod.yml file."
echo "💡 Tip: Make sure to create a .env file with your secrets before running docker-compose."
