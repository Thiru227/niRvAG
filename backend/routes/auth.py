"""
Auth Routes — Login & Session
"""
from flask import Blueprint, request, jsonify, current_app
import jwt
import bcrypt
import datetime
from models.supabase_client import get_user_by_email

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email', '').strip()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    user = get_user_by_email(email)
    if not user:
        return jsonify({"error": "Invalid email or password"}), 401

    if not user.get('password_hash'):
        return jsonify({"error": "This account cannot login with password"}), 401

    # Verify password
    if not bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
        return jsonify({"error": "Invalid email or password"}), 401

    if not user.get('is_active', True):
        return jsonify({"error": "Account is deactivated"}), 403

    # Generate JWT
    payload = {
        'id': user['id'],
        'email': user['email'],
        'name': user['name'],
        'role': user['role'],
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }
    token = jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')

    return jsonify({
        "access_token": token,
        "user": {
            "id": user['id'],
            "name": user['name'],
            "email": user['email'],
            "role": user['role'],
            "expertise": user.get('expertise')
        }
    })


@auth_bp.route('/session', methods=['POST'])
def create_session():
    """Create a customer session (name + email only, no password)."""
    data = request.get_json()
    name = data.get('name', '').strip()
    email = data.get('email', '').strip()

    if not name or not email:
        return jsonify({"error": "Name and email are required"}), 400

    return jsonify({
        "user_name": name,
        "user_email": email,
        "session": True
    })


@auth_bp.route('/logout', methods=['POST'])
def logout():
    return jsonify({"message": "Logged out"})
