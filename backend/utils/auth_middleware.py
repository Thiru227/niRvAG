"""
Auth Middleware — JWT decorator
"""
from functools import wraps
from flask import request, jsonify, g, current_app
import jwt


def require_auth(roles=None):
    """Decorator: validates JWT, optionally checks role."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = request.headers.get('Authorization', '').replace('Bearer ', '')
            if not token:
                return jsonify({"error": "Unauthorized — no token provided"}), 401

            try:
                payload = jwt.decode(
                    token,
                    current_app.config['SECRET_KEY'],
                    algorithms=['HS256']
                )
                g.user = payload  # { id, email, role, name }
            except jwt.ExpiredSignatureError:
                return jsonify({"error": "Token expired"}), 401
            except jwt.InvalidTokenError:
                return jsonify({"error": "Invalid token"}), 401

            if roles and g.user.get('role') not in roles:
                return jsonify({"error": "Forbidden — insufficient role"}), 403

            return f(*args, **kwargs)
        return decorated
    return decorator
