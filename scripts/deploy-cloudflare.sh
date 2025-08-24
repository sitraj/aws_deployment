#!/bin/bash

# Deploy with CloudFlare SSL (free and automatic)
# Just point your domain to CloudFlare and get free SSL

set -e

echo "🚀 Starting deployment with CloudFlare SSL..."

# Get environment variables
DOMAIN=${DOMAIN:-"app.sritraj.com"}

echo "🌐 Domain: $DOMAIN"

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker stop flask-app 2>/dev/null || true
docker rm flask-app 2>/dev/null || true

# Build and run Flask app
echo "🔨 Building and starting Flask application..."
docker build -t flask-app .

docker run -d --name flask-app \
  -p 8080:8080 \
  -e FLASK_ENV=production \
  -e APP_NAME=flask-app \
  -e APP_VERSION=1.0.0 \
  -e LOG_LEVEL=INFO \
  -e HEALTH_CHECK_ENABLED=true \
  -e CORS_ENABLED=false \
  -e HTTPS_ENABLED=false \
  flask-app

echo "✅ Flask app running on HTTP (port 8080)"

# Test the application
echo "🧪 Testing application..."
sleep 5
if curl -f "http://localhost:8080/health" > /dev/null 2>&1; then
    echo "✅ Application is working"
else
    echo "❌ Application is not responding"
    exit 1
fi

echo ""
echo "🎉 Deployment completed!"
echo "📊 Summary:"
echo "   - Domain: $DOMAIN"
echo "   - HTTP: http://$DOMAIN:8080"
echo "   - HTTPS: Configure CloudFlare for free SSL"
echo ""
echo "🔧 Next steps for HTTPS with CloudFlare:"
echo "   1. Sign up for free CloudFlare account"
echo "   2. Add your domain to CloudFlare"
echo "   3. Update your domain's nameservers to CloudFlare"
echo "   4. Create an A record pointing to your EC2 IP: $DOMAIN → 54.172.21.16"
echo "   5. Enable 'Always Use HTTPS' in CloudFlare SSL settings"
echo "   6. Your site will be available at https://$DOMAIN"
echo ""
echo "📋 Container status:"
docker ps | grep flask-app

echo ""
echo "📋 Recent logs:"
docker logs --tail=10 flask-app
