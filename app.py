from flask import Flask, jsonify, request
import os
import logging
import json
import time
from datetime import datetime
from werkzeug.exceptions import HTTPException
from config import config
from flask_talisman import Talisman

# Get configuration based on environment
config_name = os.environ.get('FLASK_ENV', 'production')
app_config = config.get(config_name, config['default'])

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
        force_https=True,
        strict_transport_security=True,
        strict_transport_security_max_age=31536000,
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
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/security-headers')
def get_security_headers():
    """Get current security headers (for testing)"""
    logger.info('Security headers requested')
    return jsonify({
        'message': 'Security headers are active',
        'environment': app_config.ENVIRONMENT,
        'timestamp': datetime.utcnow().isoformat()
    })

if __name__ == '__main__':
    logger.info('Starting Flask application', extra={
        'port': app_config.PORT,
        'environment': app_config.ENVIRONMENT,
        'app_name': app_config.APP_NAME,
        'version': app_config.APP_VERSION
    })
    app.run(host=app_config.HOST, port=app_config.PORT, debug=app_config.DEBUG)

