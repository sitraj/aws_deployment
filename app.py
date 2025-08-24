from flask import Flask, jsonify, request
import os
import logging
from pythonjsonlogger import jsonlogger
import time
from datetime import datetime

# Disable Werkzeug's default logging
logging.getLogger('werkzeug').disabled = True

# Configure structured logging
logger = logging.getLogger()
logger.handlers.clear()  # Clear any existing handlers
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter(
    fmt='%(timestamp)s %(level)s %(name)s %(message)s'
)
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

@app.errorhandler(Exception)
def handle_exception(e):
    """Log exceptions with structured format"""
    logger.error('Unhandled exception', extra={
        'exception_type': type(e).__name__,
        'exception_message': str(e),
        'path': request.path,
        'method': request.method
    })
    return jsonify({
        'error': 'Internal server error',
        'status': 'error'
    }), 500

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

