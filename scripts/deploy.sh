#!/bin/bash

# Automated deployment script with SSL setup
# This script handles the complete deployment process including SSL certificate generation

set -e

echo "🚀 Starting automated deployment with SSL setup..."

# Check if we're already in the app directory
if [ ! -f "app.py" ] || [ ! -f "requirements.txt" ]; then
  echo "📥 Repository not found in current directory, cloning..."
  # Clone or update repo
  if [ ! -d ~/app ]; then
    git clone https://github.com/$GITHUB_REPOSITORY ~/app
  fi
  cd ~/app
  git pull origin main
else
  echo "✅ Already in app directory, proceeding with deployment..."
  # Make sure we're on the latest version
  git pull origin main
fi

# Stop and remove existing container if it exists
echo "🛑 Stopping existing container..."
docker stop flask-app || true
docker rm flask-app || true

# Build new container
echo "🔨 Building new container..."
docker build -t flask-app .

# Check if domain is configured and is a valid domain (not IP)
if [ -z "$DOMAIN" ]; then
  echo "⚠️ No domain configured, deploying without SSL..."
  echo "🔍 To enable HTTPS, set the DOMAIN environment variable"
  DEPLOY_HTTPS=false
elif [[ "$DOMAIN" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "⚠️ IP address detected: $DOMAIN"
  echo "🔍 Let's Encrypt requires a domain name, not an IP address"
  echo "🔍 Generating self-signed certificate for HTTPS access"
  DEPLOY_HTTPS=true
  
  # Generate self-signed certificate for IP address
  echo "🔐 Setting up self-signed SSL certificate..."
  chmod +x scripts/generate_self_signed.sh
  ./scripts/generate_self_signed.sh
else
  echo "🌐 Domain configured: $DOMAIN"
  DEPLOY_HTTPS=true
fi

# Check if email is configured
if [ -z "$EMAIL" ]; then
  echo "⚠️ No email configured for SSL certificates"
  DEPLOY_HTTPS=false
else
  echo "📧 Email configured: $EMAIL"
fi

# SSL certificate paths
SSL_CERT_PATH="/etc/letsencrypt/live/$DOMAIN/fullchain.pem"
SSL_KEY_PATH="/etc/letsencrypt/live/$DOMAIN/privkey.pem"

# Check if SSL certificates already exist
if [ "$DEPLOY_HTTPS" = true ] && [ -f "$SSL_CERT_PATH" ] && [ -f "$SSL_KEY_PATH" ]; then
  echo "✅ SSL certificates found, using existing certificates..."
  CERTIFICATES_EXIST=true
else
  echo "🔍 SSL certificates not found, will attempt to generate..."
  CERTIFICATES_EXIST=false
fi

# Function to detect and install certbot
install_certbot() {
  echo "🔍 Detecting package manager..."
  
  # Detect the package manager
  if command -v apt-get &> /dev/null; then
    echo "📦 Using apt-get (Ubuntu/Debian)"
    sudo apt-get update
    sudo apt-get install -y certbot
  elif command -v yum &> /dev/null; then
    echo "📦 Using yum (Amazon Linux/RHEL/CentOS)"
    sudo yum update -y
    # Install EPEL repository for Amazon Linux 2
    sudo yum install -y epel-release
    sudo yum install -y certbot
  elif command -v dnf &> /dev/null; then
    echo "📦 Using dnf (Fedora/RHEL 8+)"
    sudo dnf update -y
    sudo dnf install -y certbot
  elif command -v snap &> /dev/null; then
    echo "📦 Using snap"
    sudo snap install --classic certbot
    sudo ln -s /snap/bin/certbot /usr/bin/certbot
  else
    echo "❌ No supported package manager found"
    echo "🔧 Trying pip installation..."
    if command -v pip3 &> /dev/null; then
      sudo pip3 install certbot
    elif command -v pip &> /dev/null; then
      sudo pip install certbot
    else
      echo "⚠️ Please install certbot manually and try again"
      return 1
    fi
  fi
}

# Attempt to generate SSL certificates if needed
if [ "$DEPLOY_HTTPS" = true ] && [ "$CERTIFICATES_EXIST" = false ]; then
  echo "🔐 Attempting to generate SSL certificates..."
  
  # Install certbot if not already installed
  if ! command -v certbot &> /dev/null; then
    echo "📦 Installing certbot..."
    if ! install_certbot; then
      echo "❌ Failed to install certbot"
      echo "⚠️ Continuing deployment without SSL..."
      CERTIFICATES_EXIST=false
    fi
  else
    echo "✅ Certbot already installed"
  fi

  # Only proceed if certbot is available
  if command -v certbot &> /dev/null; then
    # Create webroot directory for certificate verification
    sudo mkdir -p /var/www/html/.well-known/acme-challenge
    sudo chown -R www-data:www-data /var/www/html 2>/dev/null || sudo chown -R nginx:nginx /var/www/html 2>/dev/null || true

    # Stop any existing web server temporarily
    sudo systemctl stop nginx 2>/dev/null || true
    sudo systemctl stop apache2 2>/dev/null || true
    sudo systemctl stop httpd 2>/dev/null || true

    # Generate SSL certificate using standalone method
    echo "🔐 Generating SSL certificate for $DOMAIN..."
    if sudo certbot certonly --standalone --email="$EMAIL" --agree-tos --no-eff-email --domains="$DOMAIN" --non-interactive; then
      echo "✅ SSL certificate generated successfully!"
      CERTIFICATES_EXIST=true
      
      # Set proper permissions
      sudo chmod 644 "$SSL_CERT_PATH"
      sudo chmod 600 "$SSL_KEY_PATH"
      
      # Create renewal hook
      sudo mkdir -p /etc/letsencrypt/renewal-hooks/post
      sudo tee /etc/letsencrypt/renewal-hooks/post/restart-docker.sh > /dev/null << 'RENEWAL_HOOK'
#!/bin/bash
echo "🔄 Restarting Docker container after certificate renewal..."
docker restart flask-app 2>/dev/null || true
echo "✅ Docker container restarted successfully"
RENEWAL_HOOK
      sudo chmod +x /etc/letsencrypt/renewal-hooks/post/restart-docker.sh
      
    else
      echo "❌ Failed to generate SSL certificate"
      echo "⚠️ Continuing deployment without SSL..."
      CERTIFICATES_EXIST=false
    fi
  else
    echo "❌ Certbot not available"
    echo "⚠️ Continuing deployment without SSL..."
    CERTIFICATES_EXIST=false
  fi
fi

# Deploy based on SSL certificate availability
if [ "$CERTIFICATES_EXIST" = true ]; then
  echo "✅ Deploying with HTTPS..."
  
  # Start container with HTTPS on port 443
  docker run -d --name flask-app \
    -p 443:443 \
    -v "$SSL_CERT_PATH:/app/cert.pem:ro" \
    -v "$SSL_KEY_PATH:/app/key.pem:ro" \
    -e FLASK_ENV=production \
    -e APP_NAME=flask-app \
    -e APP_VERSION=1.0.0 \
    -e LOG_LEVEL=INFO \
    -e HEALTH_CHECK_ENABLED=true \
    -e CORS_ENABLED=false \
    -e HTTPS_ENABLED=true \
    -e SSL_CERT_PATH=/app/cert.pem \
    -e SSL_KEY_PATH=/app/key.pem \
    flask-app
    
  echo "🌐 Application deployed on HTTPS (port 443)"
  
  # Wait for container to start
  echo "⏳ Waiting for container to start..."
  sleep 15
  
  # Test HTTPS endpoints
  echo "🧪 Testing HTTPS endpoints..."
  for endpoint in health metrics config security-headers ssl-status force-https-test; do
    if curl -k -f "https://localhost:443/$endpoint" > /dev/null 2>&1; then
      echo "✅ HTTPS $endpoint endpoint is responding"
    else
      echo "❌ HTTPS $endpoint endpoint is not responding"
      exit 1
    fi
  done
  
else
  echo "⚠️ Deploying without HTTPS..."
  
  # Start container without HTTPS on port 8080
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
    
  echo "🌐 Application deployed on HTTP (port 8080)"
  
  # Wait for container to start
  echo "⏳ Waiting for container to start..."
  sleep 10
  
  # Test HTTP endpoints
  echo "🧪 Testing HTTP endpoints..."
  for endpoint in health metrics config security-headers ssl-status; do
    if curl -f "http://localhost:8080/$endpoint" > /dev/null 2>&1; then
      echo "✅ HTTP $endpoint endpoint is responding"
    else
      echo "❌ HTTP $endpoint endpoint is not responding"
      exit 1
    fi
  done
fi

# Verify container is running
if docker ps | grep -q flask-app; then
  echo "✅ Docker container is running successfully"
else
  echo "❌ Docker container failed to start"
  exit 1
fi

# Show deployment summary
echo ""
echo "🎉 Deployment completed successfully!"
echo "📊 Deployment Summary:"
echo "   - Domain: $DOMAIN"
echo "   - HTTPS Enabled: $CERTIFICATES_EXIST"
echo "   - Container Status: Running"

if [ "$CERTIFICATES_EXIST" = true ]; then
  if [[ "$DOMAIN" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "   - Access URL: https://$DOMAIN"
    echo "   - SSL Certificate: Self-signed (browsers will show security warning)"
  else
    echo "   - Access URL: https://$DOMAIN"
    echo "   - SSL Certificate: Auto-renewing (every 60 days)"
  fi
else
  echo "   - Access URL: http://$EC2_HOST:8080"
  echo "   - SSL Certificate: Not configured"
fi

echo ""
echo "📋 Recent application logs:"
docker logs --tail 5 flask-app

echo ""
echo "🔍 Container status:"
docker ps | grep flask-app
