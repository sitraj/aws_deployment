import os
from datetime import datetime

class Config:
    """Base configuration class"""
    APP_NAME = os.environ.get('APP_NAME', 'flask-app')
    APP_VERSION = os.environ.get('APP_VERSION', '1.0.0')
    ENVIRONMENT = os.environ.get('FLASK_ENV', 'production')
    DEBUG = os.environ.get('DEBUG', 'false').lower() == 'true'
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 8080))
    
    # Feature flags
    HEALTH_CHECK_ENABLED = os.environ.get('HEALTH_CHECK_ENABLED', 'true').lower() == 'true'
    CORS_ENABLED = os.environ.get('CORS_ENABLED', 'false').lower() == 'true'
    
    # HTTPS Configuration
    HTTPS_ENABLED = os.environ.get('HTTPS_ENABLED', 'false').lower() == 'true'
    SSL_CERT_PATH = os.environ.get('SSL_CERT_PATH', None)
    SSL_KEY_PATH = os.environ.get('SSL_KEY_PATH', None)
    
    def get_health_response(self):
        """Generate health check response"""
        return {
            'status': 'healthy',
            'service': self.APP_NAME,
            'version': self.APP_VERSION,
            'environment': self.ENVIRONMENT,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def get_metrics_response(self):
        """Generate metrics response"""
        return {
            'uptime': 'running',
            'requests_processed': 'tracked_in_logs',
            'environment': self.ENVIRONMENT,
            'version': self.APP_VERSION,
            'timestamp': datetime.utcnow().isoformat()
        }

class DevelopmentConfig(Config):
    """Development configuration"""
    ENVIRONMENT = 'development'
    DEBUG = True
    LOG_LEVEL = 'DEBUG'
    HEALTH_CHECK_ENABLED = True
    CORS_ENABLED = True
    HTTPS_ENABLED = False

class TestingConfig(Config):
    """Testing configuration"""
    ENVIRONMENT = 'testing'
    DEBUG = True
    LOG_LEVEL = 'DEBUG'
    HEALTH_CHECK_ENABLED = True
    CORS_ENABLED = False
    HTTPS_ENABLED = False

class ProductionConfig(Config):
    """Production configuration"""
    ENVIRONMENT = 'production'
    DEBUG = False
    LOG_LEVEL = 'INFO'
    HEALTH_CHECK_ENABLED = True
    CORS_ENABLED = False
    # HTTPS_ENABLED will be set via environment variable
    # SSL_CERT_PATH and SSL_KEY_PATH will be set via environment variables

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': ProductionConfig
}
