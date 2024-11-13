from flask import Blueprint, request, jsonify, current_app, make_response, after_this_request
import requests
from utils.extensions import cache
import uuid  # Import the uuid module for generating session ID
import time
import random
import secrets
from functools import wraps
import traceback

validate_bp = Blueprint('validate', __name__)

def require_verification(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            current_app.logger.info("Entering require_verification decorator")
            session_id = request.headers.get('Session-ID')
            verify_token = request.headers.get('Verification-Token')

            # Log the received headers
            current_app.logger.info(f"Headers: {dict(request.headers)}")

            current_app.logger.info(f"Session ID: {session_id}, Verification Token: {verify_token}")

            if not session_id or not verify_token:
                current_app.logger.warning("Missing session ID or validation token")
                return jsonify({"error": "Missing session ID or validation token"}), 401

#            current_app.logger.info(f"Attempting to retrieve token for session {session_id}")
#            stored_token = cache.get(f"{session_id}_verification_token")
#            current_app.logger.info(f"Retrieved token: {stored_token}")

#            if not stored_token or stored_token != verify_token:
#                return jsonify({"error": "Invalid or expired verification token"}), 401

            current_app.logger.info("Verification successful, proceeding to route")

            # Call the wrapped function with the original arguments
            return f(*args, **kwargs)
        except Exception as e:
            current_app.logger.error(f"Exception in require_verification decorator: {str(e)}")
            current_app.logger.error(traceback.format_exc())  # Logs the full stack trace
            return jsonify({"error": "Internal server error"}), 500
    return decorated_function

# New decorator for nonce validation
def validate_nonce(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        session_id = request.headers.get("Session-ID")
        request_nonce = request.headers.get("X-CSP-Nonce")
        current_app.logger.info(f"Session ID: {session_id}, Request Nonce: {request_nonce}")

        if not request_nonce:
            current_app.logger.info(f"Session ID: {session_id}, Missing request nonce")
            return jsonify({"error": "Missing nonce"}), 401

        stored_nonce = cache.get(f"{session_id}_verify_nonce")
        current_app.logger.info(f"Session ID: {session_id}, Stored Nonce: {stored_nonce}")
        if not stored_nonce or stored_nonce != request_nonce:
            return jsonify({"error": "Invalid or expired nonce"}), 401

        # Generate a new nonce for the next request
        validate_nonce = secrets.token_urlsafe(16)
        cache.set(f"{session_id}_validate_nonce", validate_nonce, timeout=3600)

        # Attach the new nonce to the response
        @after_this_request
        def attach_new_nonce(response):
            response.headers['X-CSP-Nonce'] = validate_nonce
            return response

        return f(*args, **kwargs)
    return decorated_function

@validate_bp.route('/api/validate', methods=['OPTIONS'])
def cors_preflight():
    current_app.logger.info(f"Incoming headers: {dict(request.headers)}")
    # Handle OPTIONS preflight requests directly (no need for verification or nonce validation)
    if request.method == 'OPTIONS':
        origin = request.headers.get('Origin')
        if origin in ["https://uhsvtsdohdapp01.utmck.edu", "https://sdohtest.utmck.edu"]:
            response = make_response('', 204)  # No Content for preflight requests
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, Session-ID, Verification-Token, Validation-Token, X-CSP-Nonce'
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            return response
        else:
            return make_response('Forbidden', 403)


# Secure method for all other methods (POST, GET, HEAD), use require_verification and validate_nonce decorators
# Ensure the next function only runs with requests to */api/validate AND only with methods listed.
@validate_bp.route('/api/validate', methods=['POST', 'GET', 'HEAD'])
@require_verification
@validate_nonce
def validate():
    current_app.logger.info(f"Incoming headers: {dict(request.headers)}")
    if request.method == 'GET':
        return jsonify({'message': 'GET method not allowed for this endpoint'}), 405

    if request.method == 'HEAD':
        current_app.logger.info("Received HEAD request")
        return '', 200

    if request.method == 'OPTIONS':
        origin = request.headers.get('Origin')
        if origin in ["https://uhsvtsdohdapp01.utmck.edu", "https://sdohtest.utmck.edu"]:
            response = make_response('', 204)  # No Content for preflight requests
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, Session-Id, Verification-Token, Validation-Token, X-CSP-Nonce'
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            return response
        else:
            return make_response('Forbidden', 403)

    if request.method == 'POST':
        if request.content_type != 'application/json':
            return jsonify({"error": "Unsupported Media Type"}), 415

        data = request.json
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        session_id = request.headers.get("Session-ID")
        verification_token = request.headers.get("Verification-Token")
        address_choice = data.get("address")
#add
        request_nonce = request.headers.get("X-CSP-Nonce")
        current_app.logger.info(f"Session ID: {session_id}")
        current_app.logger.info(f"Request Data: {data}")
        current_app.logger.info(f"Address Chosen: {address_choice}")
#add
        current_app.logger.info(f"Request Nonce: {request_nonce}")

        if not all([session_id, address_choice, verification_token]):
            if not verification_token:
                return jsonify({"error": "User invalid visit verification"}), 400
            if not session_id:
                return jsonify({"error": "Session ID missing in headers"}), 400
            if not address_choice:
                return jsonify({"error": "Address choice missing in request body"}), 400

        # Get the correct address from cache
        correct_address = cache.get(f"{session_id}_correct_address")
        current_app.logger.info(f"Correct Address: {correct_address}")

        if not correct_address:
            # If there's no correct address in cache, the session is invalid
            cache.delete(f"{session_id}_correct_address")
            # Clean up any other session data if necessary
            # cache.delete(f"{session_id}_"
            return jsonify({"error": "Invalid or expired session"}), 400

        if address_choice == correct_address:
            # User passed validation, deleting cache address because they would need to start over the validation process to go again
            cache.delete(f"{session_id}_correct_address")
            # Clean up other session data if necessary
            cache.delete(f"{session_id}_tries")  # Reset tries on successful verification
            return jsonify({
                "message": "Address validated successfully",
                "session_id": session_id,
                "isValidated": True,
                "validationToken": generate_validation_token(session_id)
            }), 200
        else:
            # User failed validation
            cache.delete(f"{session_id}_correct_address")  # Clean up session data
            return jsonify({
                "error": "Address validation failed",
                "redirect": "/validation-failed",
                "isValidated": False
            }), 400


# Protected API route using decorator
@validate_bp.route('/api/protected-route', methods=['POST'])
@require_verification
@validate_nonce
def protected_route():
    # This route can only be accessed with a valid session ID and validation token
    return jsonify({"message": "Access granted to protected validation route"}), 200


def generate_validation_token(session_id):
    # Generate a secure token
    valtoken = secrets.token_urlsafe(32)
    # Store the token in cache with an expiration time
    cache.set(f"{session_id}_validation_token", valtoken, timeout=3600)  # 1 hour expiration
    return valtoken

