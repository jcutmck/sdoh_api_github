import os
from dotenv import load_dotenv

print("I made it into the config file!")

class Config:
    FLASK_ENV =os.getenv('FLASK_ENV')
    SECRET_KEY = os.getenv('SECRET_KEY')
    FLASK_DEBUG = os.getenv('FLASK_DEBUG')
    ENV_CERT_FILE = os.getenv('ENV_CERT_FILE')
    ENV_KEY_FILE = os.getenv('ENV_KEY_FILE')
    FS_TOK = os.getenv('FS_BEAR_TOKEN')
    FS_API = os.getenv('FS_API_URL')
    CP_API = os.getenv('ENV_CP_API_URL')


class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

def load_environment():
    environment = os.getenv('FLASK_ENV', 'development')
    if environment == 'production':
        print("Loading .env.production")
        load_dotenv('.env.production')
    else:
        print("Loading .env.development")
        load_dotenv('.env.development')
