#!/bin/bash

# Deploy using AWS Certificate Manager (ACM)
# This is the most reliable approach for AWS environments

set -e

echo "🚀 Starting deployment with AWS Certificate Manager..."

# Get environment variables
DOMAIN=${DOMAIN:-"app.sritraj.com"}
EMAIL=${EMAIL:-"admin@example.com"}

echo "🌐 Domain: $DOMAIN"
echo "📧 Email: $EMAIL"

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker stop flask-app 2>/dev/null || true
docker rm flask-app 2>/dev/null || true

# Build and run Flask app on HTTP only
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
echo "   - HTTPS: Use AWS Application Load Balancer or CloudFront"
echo ""
echo "🔧 Next steps for HTTPS:"
echo "   1. Create an Application Load Balancer in AWS"
echo "   2. Request a certificate in AWS Certificate Manager"
echo "   3. Configure the ALB to use HTTPS and forward to port 8080"
echo "   4. Update your DNS to point to the ALB"
echo ""
echo "📋 Container status:"
docker ps | grep flask-app

echo ""
echo "📋 Recent logs:"
docker logs --tail=10 flask-app
