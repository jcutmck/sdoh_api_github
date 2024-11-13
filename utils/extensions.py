# extensions.py
import secrets
from flask import request, jsonify
from functools import wraps
from flask_caching import Cache

cache = Cache()

def generate_csp_nonce():
    return secrets.token_urlsafe(16)

def get_csp_nonce():
    # Generate a new nonce for each request
    return generate_csp_nonce()

def validate_nonce(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        session_id = request.headers.get('Session-ID')
        client_nonce = request.headers.get('X-CSP-Nonce')

        if not session_id or not client_nonce:
            return jsonify({'error': 'Missing session ID or nonce'}), 403

        session_data = cache.get(session_id)
        if not session_data or session_data.get('nonce') != client_nonce:
            return jsonify({'error': 'Invalid session or nonce'}), 403

        return f(*args, **kwargs)
    return decorated_function
