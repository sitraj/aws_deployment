from flask import Flask, jsonify, request
import os
import logging
import json
import time
from datetime import datetime

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
logger.setLevel(logging.INFO)

app = Flask(__name__)

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

@app.route('/')
def hello():
    logger.info('Hello endpoint called')
    return 'Hello, World!!!'

@app.route('/health')
def health_check():
    logger.info('Health check requested')
    return jsonify({
        'status': 'healthy',
        'service': 'flask-app',
        'version': '1.0.0',
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/metrics')
def metrics():
    """Basic metrics endpoint"""
    logger.info('Metrics endpoint called')
    return jsonify({
        'uptime': 'running',
        'requests_processed': 'tracked_in_logs',
        'timestamp': datetime.utcnow().isoformat()
    })

if __name__ == '__main__':
    logger.info('Starting Flask application', extra={
        'port': int(os.environ.get('PORT', 8080)),
        'environment': os.environ.get('FLASK_ENV', 'production')
    })
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)

