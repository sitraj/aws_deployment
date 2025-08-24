#!/bin/bash

# Simple deployment script using Docker Compose
# This approach is much more reliable than trying to install certbot on Amazon Linux 2

set -e

echo "🚀 Starting deployment with Docker Compose..."

# Get environment variables
DOMAIN=${DOMAIN:-"app.sritraj.com"}
EMAIL=${EMAIL:-"admin@example.com"}

echo "🌐 Domain: $DOMAIN"
echo "📧 Email: $EMAIL"

# Install Docker Compose if not available
DOCKER_COMPOSE_CMD="docker-compose"
if ! command -v docker-compose &> /dev/null; then
    echo "🔧 Installing Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    sudo ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose
    echo "✅ Docker Compose installed"
    DOCKER_COMPOSE_CMD="/usr/local/bin/docker-compose"
fi

# Stop any existing containers
echo "🛑 Stopping existing containers..."
$DOCKER_COMPOSE_CMD down 2>/dev/null || true
docker stop flask-app nginx-proxy certbot 2>/dev/null || true
docker rm flask-app nginx-proxy certbot 2>/dev/null || true

# Build the Flask app
echo "🔨 Building Flask application..."
$DOCKER_COMPOSE_CMD build flask-app

# Start services without SSL first
echo "🚀 Starting services..."
$DOCKER_COMPOSE_CMD up -d flask-app nginx

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check if services are running
if ! $DOCKER_COMPOSE_CMD ps | grep -q "Up"; then
    echo "❌ Services failed to start"
    $DOCKER_COMPOSE_CMD logs
    exit 1
fi

echo "✅ Services started successfully"

# Test HTTP access
echo "🧪 Testing HTTP access..."
if curl -f "http://localhost/health" > /dev/null 2>&1; then
    echo "✅ HTTP is working"
else
    echo "❌ HTTP is not working"
    exit 1
fi

# Generate SSL certificate
echo "🔐 Generating SSL certificate..."
$DOCKER_COMPOSE_CMD run --rm certbot

# Reload Nginx to use SSL certificates
echo "🔄 Reloading Nginx with SSL..."
$DOCKER_COMPOSE_CMD exec nginx nginx -s reload

# Test HTTPS access
echo "🧪 Testing HTTPS access..."
sleep 5
if curl -k -f "https://localhost/health" > /dev/null 2>&1; then
    echo "✅ HTTPS is working"
else
    echo "⚠️ HTTPS not working yet, but HTTP is available"
fi

# Show deployment summary
echo ""
echo "🎉 Deployment completed!"
echo "📊 Summary:"
echo "   - Domain: $DOMAIN"
echo "   - HTTP: http://$DOMAIN"
echo "   - HTTPS: https://$DOMAIN"
echo "   - SSL Certificate: Auto-renewing"
echo ""
echo "📋 Container status:"
$DOCKER_COMPOSE_CMD ps

echo ""
echo "📋 Recent logs:"
$DOCKER_COMPOSE_CMD logs --tail=10
