#!/usr/bin/env bash
set -euo pipefail

DOMAIN="fai.mariuszderda.pl"
EMAIL="mariusz.derda@gmail.com"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

echo "=== FAI Deployment Script ==="

# 1. Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com | sh
    sudo usermod -aG docker "$USER"
    echo "Docker installed. Log out and back in, then re-run this script."
    exit 0
fi

# 2. Install docker-compose plugin if not present
if ! docker compose version &> /dev/null; then
    echo "Installing Docker Compose plugin..."
    sudo apt-get update
    sudo apt-get install -y docker-compose-plugin
fi

# 3. Create required directories
mkdir -p certbot/www certbot/conf runtime/artifacts runtime/audit runtime/reports nginx/conf.d

# 4. Bootstrap MITRE dataset
if [ ! -f data/mitre/enterprise-attack.json ]; then
    echo "Downloading MITRE ATT&CK dataset..."
    bash scripts/bootstrap.sh
fi

# 5. Copy env file
if [ ! -f .env.production ]; then
    cp .env.production.example .env.production
    echo "EDIT .env.production with your real API keys before continuing!"
    exit 1
fi

# 6. Initial cert setup (HTTP only first)
echo "Obtaining Let's Encrypt certificate..."
cat > nginx/conf.d/default.conf << 'NGINX'
server {
    listen 80;
    server_name DOMAIN_PLACEHOLDER;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 200 'FAI cert setup in progress';
    }
}
NGINX
sed -i "s/DOMAIN_PLACEHOLDER/${DOMAIN}/g" nginx/conf.d/default.conf

docker compose -f docker-compose.prod.yml up -d nginx

# Run certbot
docker run --rm \
    -v "$(pwd)/certbot/www:/var/www/certbot" \
    -v "$(pwd)/certbot/conf:/etc/letsencrypt" \
    certbot/certbot certonly --webroot \
    --webroot-path=/var/www/certbot \
    --email "$EMAIL" --agree-tos --no-eff-email \
    -d "$DOMAIN"

# 7. Deploy with full HTTPS config
echo "Starting FAI with HTTPS..."
docker compose -f docker-compose.prod.yml down

git checkout -- nginx/conf.d/default.conf

docker compose -f docker-compose.prod.yml up -d --build

echo ""
echo "=== FAI deployed at https://${DOMAIN} ==="
echo "Check: curl -I https://${DOMAIN}"

