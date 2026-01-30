"""
Configuration classes for the Flask application.
Supports different environments: development, production, testing.
"""

import os
from dotenv import load_dotenv

load_dotenv()

class BaseConfig:
    """Base configuration - shared across all environments"""
    
    # Flask Settings
    SECRET_KEY = os.getenv('SECRET_KEY')
    
    # Email Settings
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = ('Yolingo Destek', 'yolingo.proje.destek@gmail.com')
    
    # File Upload Settings
    UPLOAD_FOLDER = 'static/img'
    PROFILE_UPLOAD_FOLDER = 'static/img/profiles'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    @staticmethod
    def init_app(app):
        """Initialize application with configuration"""
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        os.makedirs(app.config['PROFILE_UPLOAD_FOLDER'], exist_ok=True)


class DevelopmentConfig(BaseConfig):
    """Development environment configuration"""
    DEBUG = True
    TESTING = False
    
    # Development-specific settings
    EXPLAIN_TEMPLATE_LOADING = False  # Set to True for template debugging


class ProductionConfig(BaseConfig):
    """Production environment configuration"""
    DEBUG = False
    TESTING = False
    
    # Override with environment variables for security
    SECRET_KEY = os.getenv('SECRET_KEY')  # Must be set in production!
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')  # Must be set in production!
    
    @classmethod
    def init_app(cls, app):
        BaseConfig.init_app(app)
        
        # Production-specific initialization
        if not cls.SECRET_KEY:
            raise ValueError("SECRET_KEY environment variable must be set in production!")
        if not cls.MAIL_PASSWORD:
            raise ValueError("MAIL_PASSWORD environment variable must be set in production!")


class TestingConfig(BaseConfig):
    """Testing environment configuration"""
    DEBUG = True
    TESTING = True
    
    # Use in-memory database for testing
    WTF_CSRF_ENABLED = False  # Disable CSRF for testing


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
