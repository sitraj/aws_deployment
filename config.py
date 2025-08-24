import os
from datetime import datetime

class Config:
    """Base configuration class"""
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Application settings
    APP_NAME = os.environ.get('APP_NAME', 'flask-app')
    APP_VERSION = os.environ.get('APP_VERSION', '1.0.0')
    ENVIRONMENT = os.environ.get('FLASK_ENV', 'production')
    
    # Server settings
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 8080))
    
    # Logging settings
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    
    # Health check settings
    HEALTH_CHECK_ENABLED = os.environ.get('HEALTH_CHECK_ENABLED', 'true').lower() == 'true'
    
    # Security settings
    CORS_ENABLED = os.environ.get('CORS_ENABLED', 'false').lower() == 'true'
    
    @classmethod
    def get_health_response(cls):
        """Get health check response with configurable values"""
        return {
            'status': 'healthy',
            'service': cls.APP_NAME,
            'version': cls.APP_VERSION,
            'environment': cls.ENVIRONMENT,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    @classmethod
    def get_metrics_response(cls):
        """Get metrics response with configurable values"""
        return {
            'uptime': 'running',
            'requests_processed': 'tracked_in_logs',
            'environment': cls.ENVIRONMENT,
            'version': cls.APP_VERSION,
            'timestamp': datetime.utcnow().isoformat()
        }

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    ENVIRONMENT = 'development'
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    ENVIRONMENT = 'production'
    LOG_LEVEL = 'INFO'

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    ENVIRONMENT = 'testing'
    LOG_LEVEL = 'DEBUG'

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': ProductionConfig
}
