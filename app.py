from flask import Flask, jsonify, request, redirect, url_for
import os
import logging
import json
import time
from datetime import datetime
from werkzeug.exceptions import HTTPException
from config import config
from flask_talisman import Talisman
import ssl

# Get configuration based on environment
config_name = os.environ.get('FLASK_ENV', 'production')
app_config_class = config.get(config_name, config['default'])
app_config = app_config_class()  # Create an instance

# Disable Werkzeug's default logging
logging.getLogger('werkzeug').disabled = True

# Configure structured logging
class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'name': record.name,
            'message': record.getMessage()
        }
        # Add extra fields if they exist
        if hasattr(record, 'method'):
            log_entry['method'] = record.method
        if hasattr(record, 'path'):
            log_entry['path'] = record.path
        if hasattr(record, 'remote_addr'):
            log_entry['remote_addr'] = record.remote_addr
        if hasattr(record, 'user_agent'):
            log_entry['user_agent'] = record.user_agent
        if hasattr(record, 'status_code'):
            log_entry['status_code'] = record.status_code
        if hasattr(record, 'content_length'):
            log_entry['content_length'] = record.content_length
        if hasattr(record, 'exception_type'):
            log_entry['exception_type'] = record.exception_type
        if hasattr(record, 'exception_message'):
            log_entry['exception_message'] = record.exception_message
        if hasattr(record, 'port'):
            log_entry['port'] = record.port
        if hasattr(record, 'environment'):
            log_entry['environment'] = record.environment
            
        return json.dumps(log_entry)

logger = logging.getLogger()
logger.handlers.clear()  # Clear any existing handlers
logHandler = logging.StreamHandler()
formatter = JSONFormatter()
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)
logger.setLevel(getattr(logging, app_config.LOG_LEVEL))

app = Flask(__name__)
app.config.from_object(app_config)

# Check if HTTPS is actually configured
HTTPS_ENABLED = os.environ.get('HTTPS_ENABLED', 'false').lower() == 'true'
SSL_CERT_PATH = os.environ.get('SSL_CERT_PATH', None)
SSL_KEY_PATH = os.environ.get('SSL_KEY_PATH', None)

# Verify SSL certificate files exist if HTTPS is enabled
if HTTPS_ENABLED:
    if not SSL_CERT_PATH or not SSL_KEY_PATH:
        logger.warning('HTTPS_ENABLED is true but SSL certificate paths are not provided')
        HTTPS_ENABLED = False
    elif not os.path.exists(SSL_CERT_PATH) or not os.path.exists(SSL_KEY_PATH):
        logger.warning('SSL certificate files not found at specified paths')
        HTTPS_ENABLED = False
    else:
        logger.info(f'SSL certificates found: {SSL_CERT_PATH}, {SSL_KEY_PATH}')

FORCE_HTTPS = HTTPS_ENABLED and app_config.ENVIRONMENT == 'production'

# Configure security headers based on environment
if app_config.ENVIRONMENT == 'production':
    # Production: Strict security headers
    Talisman(
        app,
        content_security_policy={
            'default-src': "'self'",
            'script-src': "'self'",
            'style-src': "'self'",
            'img-src': "'self'",
            'font-src': "'self'",
        },
        force_https=FORCE_HTTPS,  # Only force HTTPS if actually configured
        strict_transport_security=FORCE_HTTPS,  # Only HSTS if HTTPS is enabled
        strict_transport_security_max_age=31536000 if FORCE_HTTPS else None,
        frame_options='DENY'
    )
else:
    # Development/Testing: Relaxed security headers
    Talisman(
        app,
        content_security_policy=None,
        force_https=False,
        strict_transport_security=False,
        frame_options='SAMEORIGIN'
    )

@app.before_request
def log_request_info():
    """Log incoming request information"""
    logger.info('Incoming request', extra={
        'method': request.method,
        'path': request.path,
        'remote_addr': request.remote_addr,
        'user_agent': request.headers.get('User-Agent', 'Unknown')
    })

@app.after_request
def log_response_info(response):
    """Log response information"""
    logger.info('Response sent', extra={
        'status_code': response.status_code,
        'content_length': len(response.get_data()),
        'path': request.path
    })
    return response

@app.errorhandler(Exception)
def handle_exception(e):
    """Log exceptions with structured format and return appropriate responses"""
    if isinstance(e, HTTPException):
        # Handle HTTP exceptions (404, 405, etc.) with proper status codes
        logger.warning('HTTP exception', extra={
            'exception_type': type(e).__name__,
            'exception_message': str(e),
            'path': request.path,
            'method': request.method,
            'status_code': e.code
        })
        return jsonify({
            'error': e.description,
            'status': 'error',
            'status_code': e.code
        }), e.code
    else:
        # Handle other exceptions as 500 errors
        logger.error('Unhandled exception', extra={
            'exception_type': type(e).__name__,
            'exception_message': str(e),
            'path': request.path,
            'method': request.method
        })
        return jsonify({
            'error': 'Internal server error',
            'status': 'error',
            'status_code': 500
        }), 500

@app.route('/')
def hello():
    logger.info('Hello endpoint called')
    return f'Hello, World from {app_config.APP_NAME}!'

@app.route('/health')
def health_check():
    logger.info('Health check requested')
    if not app_config.HEALTH_CHECK_ENABLED:
        return jsonify({
            'status': 'disabled',
            'message': 'Health checks are disabled'
        }), 503
    
    return jsonify(app_config.get_health_response())

@app.route('/metrics')
def metrics():
    """Basic metrics endpoint"""
    logger.info('Metrics endpoint called')
    return jsonify(app_config.get_metrics_response())

@app.route('/config')
def get_config():
    """Get current configuration (read-only)"""
    logger.info('Configuration requested')
    return jsonify({
        'app_name': app_config.APP_NAME,
        'version': app_config.APP_VERSION,
        'environment': app_config.ENVIRONMENT,
        'debug': app_config.DEBUG,
        'log_level': app_config.LOG_LEVEL,
        'health_check_enabled': app_config.HEALTH_CHECK_ENABLED,
        'cors_enabled': app_config.CORS_ENABLED,
        'https_enabled': HTTPS_ENABLED,
        'force_https': FORCE_HTTPS,
        'ssl_cert_path': SSL_CERT_PATH,
        'ssl_key_path': SSL_KEY_PATH,
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/security-headers')
def get_security_headers():
    """Get current security headers (for testing)"""
    logger.info('Security headers requested')
    return jsonify({
        'message': 'Security headers are active',
        'environment': app_config.ENVIRONMENT,
        'https_enabled': HTTPS_ENABLED,
        'force_https': FORCE_HTTPS,
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/ssl-status')
def ssl_status():
    """Get SSL certificate status"""
    logger.info('SSL status requested')
    
    ssl_info = {
        'https_enabled': HTTPS_ENABLED,
        'force_https': FORCE_HTTPS,
        'certificate_path': SSL_CERT_PATH,
        'key_path': SSL_KEY_PATH,
        'certificate_exists': False,
        'key_exists': False,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    if SSL_CERT_PATH:
        ssl_info['certificate_exists'] = os.path.exists(SSL_CERT_PATH)
    if SSL_KEY_PATH:
        ssl_info['key_exists'] = os.path.exists(SSL_KEY_PATH)
    
    return jsonify(ssl_info)

@app.route('/force-https-test')
def force_https_test():
    """Test endpoint to verify HTTPS enforcement"""
    logger.info('Force HTTPS test requested')
    return jsonify({
        'message': 'This endpoint should only be accessible via HTTPS',
        'protocol': request.environ.get('wsgi.url_scheme', 'unknown'),
        'https_enabled': HTTPS_ENABLED,
        'force_https': FORCE_HTTPS,
        'timestamp': datetime.utcnow().isoformat()
    })

if __name__ == '__main__':
    logger.info('Starting Flask application', extra={
        'port': app_config.PORT,
        'environment': app_config.ENVIRONMENT,
        'app_name': app_config.APP_NAME,
        'version': app_config.APP_VERSION,
        'https_enabled': False  # Nginx handles HTTPS
    })
    
    # Flask app always runs on HTTP (port 8080)
    # Nginx handles HTTPS termination and proxies to Flask
    logger.info('Starting Flask app with HTTP (Nginx handles HTTPS)')
    app.run(host=app_config.HOST, port=app_config.PORT, debug=app_config.DEBUG)

