#!/bin/bash

# Health check script for Flask application
# This script checks if the application is responding on the appropriate port

# Check if HTTPS is enabled by looking for SSL certificates
if [ -f "/app/cert.pem" ] && [ -f "/app/key.pem" ]; then
    # HTTPS mode - check port 443
    if curl -k -f https://localhost:443/health > /dev/null 2>&1; then
        exit 0
    else
        echo "HTTPS health check failed"
        exit 1
    fi
else
    # HTTP mode - check port 8080
    if curl -f http://localhost:8080/health > /dev/null 2>&1; then
        exit 0
    else
        echo "HTTP health check failed"
        exit 1
    fi
fi
