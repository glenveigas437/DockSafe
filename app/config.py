"""
Configuration settings for DockSafe application
"""

import os
from datetime import timedelta

class Config:
    """Base configuration class"""
    
    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://docksafe:docksafe@localhost/docksafe'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Scanner Configuration
    SCANNER_TYPE = os.environ.get('SCANNER_TYPE', 'trivy')  # trivy or clair
    SCANNER_TIMEOUT = int(os.environ.get('SCANNER_TIMEOUT', 300))  # 5 minutes
    VULNERABILITY_THRESHOLD = os.environ.get('VULNERABILITY_THRESHOLD', 'HIGH')
    
    # Notification Configuration
    SLACK_WEBHOOK_URL = os.environ.get('SLACK_WEBHOOK_URL')
    TEAMS_WEBHOOK_URL = os.environ.get('TEAMS_WEBHOOK_URL')
    EMAIL_SMTP_SERVER = os.environ.get('EMAIL_SMTP_SERVER')
    EMAIL_SMTP_PORT = int(os.environ.get('EMAIL_SMTP_PORT', 587))
    EMAIL_USERNAME = os.environ.get('EMAIL_USERNAME')
    EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')
    
    # Dashboard Configuration
    DASHBOARD_REFRESH_INTERVAL = int(os.environ.get('DASHBOARD_REFRESH_INTERVAL', 30))
    MAX_SCAN_HISTORY = int(os.environ.get('MAX_SCAN_HISTORY', 1000))
    
    # Monitoring Configuration
    PROMETHEUS_ENABLED = os.environ.get('PROMETHEUS_ENABLED', 'true').lower() == 'true'
    GRAFANA_URL = os.environ.get('GRAFANA_URL')
    GRAFANA_API_KEY = os.environ.get('GRAFANA_API_KEY')
    
    # File Upload Configuration
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    
    # Security Configuration
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # Logging Configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', 'docksafe.log')

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    
    # Development-specific settings
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'postgresql://docksafe:docksafe@localhost/docksafe_dev'
    
    # Enable detailed logging
    LOG_LEVEL = 'DEBUG'
    
    # Disable HTTPS requirements for development
    SESSION_COOKIE_SECURE = False

class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = False
    TESTING = True
    
    # Use in-memory SQLite for testing
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    # Disable CSRF protection for testing
    WTF_CSRF_ENABLED = False
    
    # Mock external services
    SLACK_WEBHOOK_URL = 'https://hooks.slack.com/services/TEST/TEST/TEST'
    TEAMS_WEBHOOK_URL = 'https://test.webhook.office.com/webhookb2/TEST'

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    
    # Production security settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    
    # Production logging
    LOG_LEVEL = 'WARNING'
    
    # Ensure all required environment variables are set
    @classmethod
    def init_app(cls, app):
        """Initialize production-specific settings"""
        # Log to syslog
        import logging
        from logging.handlers import SysLogHandler
        syslog_handler = SysLogHandler()
        syslog_handler.setLevel(logging.WARNING)
        app.logger.addHandler(syslog_handler)

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
