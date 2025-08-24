#!/bin/bash

# Generate self-signed SSL certificate for IP address
# This allows HTTPS access but browsers will show security warnings

echo "🔐 Generating self-signed SSL certificate for IP address..."

# Get the IP address from DOMAIN environment variable or use localhost
IP_ADDRESS=${DOMAIN:-"localhost"}

# Create SSL directory if it doesn't exist
sudo mkdir -p /etc/ssl/private
sudo mkdir -p /etc/ssl/certs

# Generate self-signed certificate
echo "📝 Creating certificate for: $IP_ADDRESS"

sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/ssl/private/self-signed.key \
    -out /etc/ssl/certs/self-signed.crt \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=$IP_ADDRESS" \
    -addext "subjectAltName=IP:$IP_ADDRESS,DNS:$IP_ADDRESS"

# Set proper permissions
sudo chmod 600 /etc/ssl/private/self-signed.key
sudo chmod 644 /etc/ssl/certs/self-signed.crt

# Create symlinks for the Flask app
sudo mkdir -p /etc/letsencrypt/live/$IP_ADDRESS
sudo ln -sf /etc/ssl/certs/self-signed.crt /etc/letsencrypt/live/$IP_ADDRESS/fullchain.pem
sudo ln -sf /etc/ssl/private/self-signed.key /etc/letsencrypt/live/$IP_ADDRESS/privkey.pem

echo "✅ Self-signed certificate generated:"
echo "   Certificate: /etc/ssl/certs/self-signed.crt"
echo "   Private Key: /etc/ssl/private/self-signed.key"
echo "   Symlinked to: /etc/letsencrypt/live/$IP_ADDRESS/"
echo ""
echo "⚠️  Note: Browsers will show security warnings for self-signed certificates"
echo "   You can proceed by clicking 'Advanced' and 'Proceed to site'"
