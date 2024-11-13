import os
from flask import Flask, request, make_response
from flask_cors import CORS
from routes.routes import verify_bp
from routes.validate import validate_bp
from routes.fscommit import submit_bp
import ssl
import logging
from datetime import timedelta
from utils.extensions import cache
from config import load_environment, DevelopmentConfig, ProductionConfig
from utils.extensions import generate_csp_nonce

# Load environment variables
load_environment()

# Create Flask app instance
app = Flask(__name__)

#reload function
def reload_config():
    if os.getenv('FLASK_ENV') == 'production':
        app.config.from_object(ProductionConfig)
        print("PROD Config")
    else:
        app.config.from_object(DevelopmentConfig)
        print("DEV config")
    app.config['ENV_CERT_FILE'] = os.getenv('ENV_CERT_FILE')

# Reload configuration after loading environment variables
reload_config()

# Define SSL certificate and key file paths
#ca.crt
CERT_FILE = "/etc/pki/tls/certs/uhsvtsdohdapp01.crt" #app.config['ENV_CERT_FILE']
KEY_FILE = "/etc/pki/tls/private/uhsvtsdohdapp01.key" #app.config['ENV_KEY_FILE']

# Create SSL context
context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)

#context.load_cert_chain('/home/strawboss/sdohapi_unzip/uhsvtdohdapp01.crt',  '/home/strawboss/sdohapi_unzip/ca.key')
context.load_cert_chain(CERT_FILE, KEY_FILE)

#app.secret_key = "devkey"
#@app.context_processor
#def inject_nonce():
#    if not hasattr(g, 'nonce'):
#        g.nonce = generate_nonce()
#    return dict(nonce=g.nonce)


cache.init_app(app,config={
    'CACHE_TYPE': 'filesystem',
    'CACHE_DIR': '/home/jclutter/flask_sessions',
    'CACHE_DEFAULT_TIMEOUT': 1 * 3600  # 1 hours
})


# Enable CORS globally
CORS(app, supports_credentials=True, resources={
    r"/*": {
        "origins": [
            "https://uhsvtsdohdapp01.utmck.edu",
            "https://sdohtest.utmck.edu"
        ],
        "methods": ["POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Session-ID", "Verification-Token", "Validation-Token", "X-CSP-Nonce"],
        "supports_credentials": True
    }
})


# Disable session cookies
app.config['SESSION_COOKIE_NAME'] = None

@app.before_request
def before_request():
    app.logger.info("Flask App New request received")
    app.logger.info(f"Headers: {dict(request.headers)}")

#@app.after_request
#def add_security_headers(response):
#    nonce = g.get('nonce', '')
#    csp = f"default-src 'self'; script-src 'self' 'nonce-{nonce}'; style-src 'self' 'nonce-{nonce}'; img-src 'self' data:; object-src 'none'; base-uri 'self';"
 #   response.headers['Content-Security-Policy'] = f"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; object-src 'none'; base-uri 'self';"
#    return response

#INITIALIZE Blueprints for API Routes
app.register_blueprint(verify_bp) 
app.register_blueprint(validate_bp)
app.register_blueprint(submit_bp) 

# Set up basic configuration for other loggers
logging.basicConfig(level=logging.INFO)

# Configure CORS logger specifically
logger = logging.getLogger('flask_cors')
logger.setLevel(logging.ERROR)

# StreamHandler but control its level:
cors_handler = logging.StreamHandler()
cors_handler.setLevel(logging.ERROR)
logger.addHandler(cors_handler)

# Optionally, you can also set the 'cors' logger to ERROR level
logging.getLogger('cors').setLevel(logging.ERROR)

@app.route('/api', methods=['OPTIONS'])
def api_root():
    origin = request.headers.get('Origin')
    if origin in ["https://uhsvtsdohdapp01.utmck.edu", "https://sdohtest.utmck.edu"]:
        response = make_response('', 204)
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Methods'] = 'POST, GET, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, Session-ID, Verification-Token, Validation-Token, X-CSP-Nonce'
        response.headers['Access-Control-Allow-Credentials'] = 'true'

        # Generate and include the CSP nonce
        csp_nonce = get_csp_nonce()
        csp = f"script-src 'nonce-{csp_nonce}' 'strict-dynamic'; object-src 'none'; base-uri 'none';"
        response.headers['Content-Security-Policy'] = csp

        # Include the nonce in a custom header
        response.headers['X-CSP-Nonce'] = csp_nonce

        return response
    else:
        return make_response('Forbidden', 403)

# route to get the nonce that should persist for the user session
@app.route('/api/get-csp-nonce', methods=['GET'])
def get_csp_nonce_api():
    origin = request.headers.get('Origin')
    if origin in ["https://uhsvtsdohdapp01.utmck.edu", "https://sdohtest.utmck.edu"]:
        csp_nonce = get_csp_nonce()
        response = make_response(jsonify({'nonce': csp_nonce}))
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, Session-ID, Verification-Token, Validation-Token, X-CSP-Nonce'
        return response
    else:
        return make_response('Forbidden', 403)


if __name__ == '__main__':
#    app.run(host='uhsvtsdohdapp01.utmck.edu',ssl_context=context, debug=True)
    app.run(host='0.0.0.0',ssl_context=context, debug=False)
# SWITCH TO 0.0.0.0 FOR TESTING ONLY

