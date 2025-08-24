#!/bin/bash

# Let's Encrypt SSL Certificate Setup Script for Docker
# This script sets up SSL certificates using Let's Encrypt in a Docker environment

set -e

# Configuration
DOMAIN=${DOMAIN:-"your-domain.com"}
EMAIL=${EMAIL:-"admin@your-domain.com"}
CERT_PATH=${CERT_PATH:-"/etc/letsencrypt/live/$DOMAIN"}
DOCKER_CONTAINER=${DOCKER_CONTAINER:-"flask-app"}

echo "🔐 Setting up Let's Encrypt SSL certificates for Docker container: $DOCKER_CONTAINER"

# Check if domain is provided
if [ "$DOMAIN" = "your-domain.com" ]; then
    echo "❌ Error: Please set the DOMAIN environment variable"
    echo "Usage: DOMAIN=your-domain.com EMAIL=your-email@domain.com ./scripts/setup_ssl_docker.sh"
    exit 1
fi

# Check if email is provided
if [ "$EMAIL" = "admin@your-domain.com" ]; then
    echo "❌ Error: Please set the EMAIL environment variable"
    echo "Usage: DOMAIN=your-domain.com EMAIL=your-email@domain.com ./scripts/setup_ssl_docker.sh"
    exit 1
fi

# Install certbot if not already installed
if ! command -v certbot &> /dev/null; then
    echo "📦 Installing certbot..."
    if command -v apt-get &> /dev/null; then
        # Ubuntu/Debian
        sudo apt-get update
        sudo apt-get install -y certbot
    elif command -v yum &> /dev/null; then
        # CentOS/RHEL
        sudo yum install -y certbot
    elif command -v brew &> /dev/null; then
        # macOS
        brew install certbot
    else
        echo "❌ Error: Could not install certbot. Please install it manually."
        exit 1
    fi
fi

# Create a temporary web server for certificate verification
echo "🌐 Creating temporary web server for certificate verification..."

# Create a simple web server container for Let's Encrypt verification
cat > /tmp/webroot/.well-known/acme-challenge/test.txt << EOF
Let's Encrypt verification file
EOF

# Run a temporary nginx container for certificate verification
echo "🚀 Starting temporary nginx container for certificate verification..."
docker run -d --name temp-nginx \
    -p 80:80 \
    -v /tmp/webroot:/var/www/html \
    nginx:alpine

# Wait for nginx to start
sleep 5

# Generate SSL certificate using standalone method
echo "🔐 Generating SSL certificate for $DOMAIN..."
sudo certbot certonly \
    --standalone \
    --email="$EMAIL" \
    --agree-tos \
    --no-eff-email \
    --domains="$DOMAIN" \
    --non-interactive

# Stop temporary nginx container
echo "🛑 Stopping temporary nginx container..."
docker stop temp-nginx
docker rm temp-nginx

# Check if certificate was generated successfully
if [ -f "$CERT_PATH/fullchain.pem" ] && [ -f "$CERT_PATH/privkey.pem" ]; then
    echo "✅ SSL certificate generated successfully!"
    echo "📄 Certificate path: $CERT_PATH/fullchain.pem"
    echo "🔑 Private key path: $CERT_PATH/privkey.pem"
    
    # Set proper permissions for the certificates
    sudo chmod 644 "$CERT_PATH/fullchain.pem"
    sudo chmod 600 "$CERT_PATH/privkey.pem"
    
    # Create renewal hook to restart the Docker container
    echo "🔄 Setting up certificate renewal hook..."
    sudo mkdir -p "/etc/letsencrypt/renewal-hooks/post"
    sudo tee "/etc/letsencrypt/renewal-hooks/post/restart-docker.sh" > /dev/null << EOF
#!/bin/bash
# Restart the Docker container after certificate renewal
echo "🔄 Restarting Docker container after certificate renewal..."
docker restart $DOCKER_CONTAINER 2>/dev/null || true
echo "✅ Docker container restarted successfully"
EOF
    
    sudo chmod +x "/etc/letsencrypt/renewal-hooks/post/restart-docker.sh"
    
    # Test certificate renewal
    echo "🧪 Testing certificate renewal..."
    sudo certbot renew --dry-run
    
    echo "✅ Let's Encrypt SSL setup completed successfully!"
    echo ""
    echo "📋 Next steps:"
    echo "1. Update your Docker run command with SSL certificate volumes:"
    echo "   docker run -d --name $DOCKER_CONTAINER \\"
    echo "     -p 443:443 \\"
    echo "     -v $CERT_PATH/fullchain.pem:/app/cert.pem:ro \\"
    echo "     -v $CERT_PATH/privkey.pem:/app/key.pem:ro \\"
    echo "     -e HTTPS_ENABLED=true \\"
    echo "     -e SSL_CERT_PATH=/app/cert.pem \\"
    echo "     -e SSL_KEY_PATH=/app/key.pem \\"
    echo "     your-flask-app"
    echo ""
    echo "2. Restart your Docker container"
    echo ""
    echo "3. Certificates will auto-renew every 60 days"
    echo ""
    echo "🔍 To check certificate status:"
    echo "   sudo certbot certificates"
    
else
    echo "❌ Error: SSL certificate generation failed"
    echo "Please check the certbot logs for more details"
    exit 1
fi

# Clean up temporary files
rm -rf /tmp/webroot

echo "🎉 SSL setup completed!"
