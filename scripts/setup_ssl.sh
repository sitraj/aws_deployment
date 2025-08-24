#!/bin/bash

# Let's Encrypt SSL Certificate Setup Script
# This script sets up SSL certificates using Let's Encrypt

set -e

# Configuration
DOMAIN=${DOMAIN:-"your-domain.com"}
EMAIL=${EMAIL:-"admin@your-domain.com"}
WEBROOT_PATH=${WEBROOT_PATH:-"/var/www/html"}
CERT_PATH=${CERT_PATH:-"/etc/letsencrypt/live/$DOMAIN"}
CERT_RENEWAL_HOOK=${CERT_RENEWAL_HOOK:-"/etc/letsencrypt/renewal-hooks/post"}

echo "🔐 Setting up Let's Encrypt SSL certificates for domain: $DOMAIN"

# Check if domain is provided
if [ "$DOMAIN" = "your-domain.com" ]; then
    echo "❌ Error: Please set the DOMAIN environment variable"
    echo "Usage: DOMAIN=your-domain.com EMAIL=your-email@domain.com ./scripts/setup_ssl.sh"
    exit 1
fi

# Check if email is provided
if [ "$EMAIL" = "admin@your-domain.com" ]; then
    echo "❌ Error: Please set the EMAIL environment variable"
    echo "Usage: DOMAIN=your-domain.com EMAIL=your-email@domain.com ./scripts/setup_ssl.sh"
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

# Create webroot directory if it doesn't exist
echo "📁 Creating webroot directory: $WEBROOT_PATH"
sudo mkdir -p "$WEBROOT_PATH"

# Set proper permissions
sudo chown -R www-data:www-data "$WEBROOT_PATH" 2>/dev/null || sudo chown -R nginx:nginx "$WEBROOT_PATH" 2>/dev/null || true

# Stop any running web server temporarily
echo "🛑 Stopping web server temporarily for certificate verification..."
sudo systemctl stop nginx 2>/dev/null || sudo systemctl stop apache2 2>/dev/null || true

# Generate SSL certificate using webroot method
echo "🔐 Generating SSL certificate for $DOMAIN..."
sudo certbot certonly \
    --webroot \
    --webroot-path="$WEBROOT_PATH" \
    --email="$EMAIL" \
    --agree-tos \
    --no-eff-email \
    --domains="$DOMAIN" \
    --non-interactive

# Check if certificate was generated successfully
if [ -f "$CERT_PATH/fullchain.pem" ] && [ -f "$CERT_PATH/privkey.pem" ]; then
    echo "✅ SSL certificate generated successfully!"
    echo "📄 Certificate path: $CERT_PATH/fullchain.pem"
    echo "🔑 Private key path: $CERT_PATH/privkey.pem"
    
    # Set proper permissions for the certificates
    sudo chmod 644 "$CERT_PATH/fullchain.pem"
    sudo chmod 600 "$CERT_PATH/privkey.pem"
    
    # Create renewal hook to restart the application
    echo "🔄 Setting up certificate renewal hook..."
    sudo mkdir -p "$CERT_RENEWAL_HOOK"
    sudo tee "$CERT_RENEWAL_HOOK/restart-app.sh" > /dev/null << 'EOF'
#!/bin/bash
# Restart the Flask application after certificate renewal
echo "🔄 Restarting Flask application after certificate renewal..."
sudo systemctl restart flask-app 2>/dev/null || true
sudo docker restart flask-app 2>/dev/null || true
echo "✅ Application restarted successfully"
EOF
    
    sudo chmod +x "$CERT_RENEWAL_HOOK/restart-app.sh"
    
    # Test certificate renewal
    echo "🧪 Testing certificate renewal..."
    sudo certbot renew --dry-run
    
    echo "✅ Let's Encrypt SSL setup completed successfully!"
    echo ""
    echo "📋 Next steps:"
    echo "1. Update your application environment variables:"
    echo "   HTTPS_ENABLED=true"
    echo "   SSL_CERT_PATH=$CERT_PATH/fullchain.pem"
    echo "   SSL_KEY_PATH=$CERT_PATH/privkey.pem"
    echo ""
    echo "2. Restart your Flask application"
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

# Restart web server
echo "🔄 Restarting web server..."
sudo systemctl start nginx 2>/dev/null || sudo systemctl start apache2 2>/dev/null || true

echo "🎉 SSL setup completed!"
