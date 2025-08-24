# Security Guide

## 🔒 Security Best Practices

This document outlines security measures and best practices for this Flask application.

## 🚫 Never Commit Secrets

### What NOT to commit:
- API keys
- Database passwords
- SSH private keys
- SSL private keys
- Access tokens
- Personal information
- Configuration files with secrets

### What IS safe to commit:
- Public keys
- Configuration templates
- Documentation
- Code (without hardcoded secrets)

## 🔐 Secret Management

### Environment Variables
All sensitive configuration is stored in environment variables:

```bash
# Application Configuration
FLASK_ENV=production
APP_NAME=flask-app
APP_VERSION=1.0.0
LOG_LEVEL=INFO

# SSL Configuration
HTTPS_ENABLED=true
SSL_CERT_PATH=/path/to/cert.pem
SSL_KEY_PATH=/path/to/key.pem

# Feature Flags
HEALTH_CHECK_ENABLED=true
CORS_ENABLED=false
```

### GitHub Secrets
The following secrets are stored in GitHub repository settings:

- `EC2_SSH_KEY` - SSH private key for EC2 access
- `EC2_USER` - EC2 instance username
- `EC2_HOST` - EC2 instance hostname/IP
- `DOMAIN` - Domain name for SSL certificates

### Adding GitHub Secrets
1. Go to your GitHub repository
2. Click "Settings" → "Secrets and variables" → "Actions"
3. Click "New repository secret"
4. Add each secret with appropriate values

## 🛡️ Security Features

### 1. Security Headers
The application uses Flask-Talisman to add security headers:

- **Content Security Policy (CSP)** - Prevents XSS attacks
- **X-Frame-Options** - Prevents clickjacking
- **X-Content-Type-Options** - Prevents MIME sniffing
- **Strict-Transport-Security (HSTS)** - Forces HTTPS
- **Referrer Policy** - Controls referrer information

### 2. HTTPS Enforcement
- Automatic SSL certificate generation with Let's Encrypt
- Conditional HTTPS enforcement (only when certificates exist)
- Certificate auto-renewal every 60 days

### 3. Input Validation
- All endpoints validate input data
- Proper error handling without information leakage
- Structured logging without sensitive data

### 4. Docker Security
- Non-root user in containers
- Read-only certificate mounts
- Minimal base image (python:3.9-slim)
- Health checks for container monitoring

## 🔍 Security Testing

### Running Security Tests
```bash
# Run all tests including security tests
python3 -m pytest test_app.py -v

# Test security headers
curl -I http://localhost:8080/health

# Test SSL status
curl http://localhost:8080/ssl-status
```

### Security Headers Verification
```bash
# Check for security headers
curl -I http://localhost:8080/health | grep -E "(X-|Strict-|Content-)"
```

## 🚨 Security Checklist

### Before Deployment
- [ ] All secrets are in environment variables
- [ ] No hardcoded passwords in code
- [ ] SSL certificates are properly configured
- [ ] Security headers are enabled
- [ ] HTTPS is enforced in production
- [ ] Docker container runs as non-root user
- [ ] Health checks are configured
- [ ] Logging doesn't expose sensitive data

### Regular Maintenance
- [ ] SSL certificates are auto-renewing
- [ ] Dependencies are up to date
- [ ] Security patches are applied
- [ ] Logs are monitored for suspicious activity
- [ ] Access logs are reviewed regularly

## 🆘 Incident Response

### If Secrets are Compromised
1. **Immediate Actions:**
   - Rotate all affected secrets immediately
   - Update GitHub secrets
   - Redeploy application with new secrets
   - Check logs for unauthorized access

2. **Investigation:**
   - Review git history for exposed secrets
   - Check access logs
   - Monitor for suspicious activity
   - Document the incident

3. **Prevention:**
   - Review secret management practices
   - Implement additional security measures
   - Update security documentation

### Reporting Security Issues
If you find a security vulnerability:
1. **DO NOT** create a public issue
2. Email security details to: [your-security-email]
3. Include detailed reproduction steps
4. Allow time for investigation and fix

## 📚 Additional Resources

- [OWASP Security Guidelines](https://owasp.org/)
- [Flask Security Documentation](https://flask-security.readthedocs.io/)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [Docker Security Best Practices](https://docs.docker.com/engine/security/)

## 🔄 Security Updates

This security guide should be reviewed and updated regularly to reflect:
- New security features
- Updated best practices
- Incident learnings
- Technology changes
