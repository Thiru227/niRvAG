"""
niRvAG — AI Customer Support Platform
Flask entry point serving both API & frontend
"""
from flask import Flask, send_from_directory, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
import os

load_dotenv()

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'frontend')

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'nirvag-dev-key')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

# CORS — allow cross-origin for widget embedding
cors_origins = os.getenv('CORS_ORIGIN', '*').split(',')
CORS(app, resources={r"/api/*": {"origins": cors_origins}})


# ── Register API Blueprints FIRST (before catch-all) ──
from routes.auth import auth_bp
from routes.chat import chat_bp
from routes.tickets import tickets_bp
from routes.admin import admin_bp
from routes.upload import upload_bp
from routes.voice import voice_bp
from routes.orders import orders_bp
from routes.stt import stt_bp

app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(chat_bp, url_prefix='/api')
app.register_blueprint(tickets_bp, url_prefix='/api')
app.register_blueprint(admin_bp, url_prefix='/api/admin')
app.register_blueprint(upload_bp, url_prefix='/api/upload')
app.register_blueprint(voice_bp, url_prefix='/api')
app.register_blueprint(orders_bp, url_prefix='/api')
app.register_blueprint(stt_bp, url_prefix='/api')


# ── Public API endpoints (no auth required) ──
from models.supabase_client import get_brand_settings

@app.route('/api/health')
def health():
    return jsonify({"status": "ok", "app": "nirvag"})

@app.route('/api/widget/settings')
def widget_settings():
    """Public endpoint for chat widget — returns brand identity."""
    try:
        s = get_brand_settings()
        return jsonify({
            "brand_name": s.get('brand_name', 'niRvAG'),
            "welcome_message": s.get('welcome_message', 'Hello! How can I help?'),
            "color_primary": s.get('color_primary', '#6366f1'),
            "logo_url": s.get('logo_url', ''),
            "tone": s.get('tone', 'professional')
        })
    except Exception:
        return jsonify({"brand_name": "niRvAG", "welcome_message": "Hello! How can I help?", "color_primary": "#6366f1"})


# ── Serve Frontend (AFTER API routes, GET only) ──
@app.route('/', methods=['GET'])
def serve_index():
    return send_from_directory(FRONTEND_DIR, 'index.html')

@app.route('/pages/<path:filename>', methods=['GET'])
def serve_pages(filename):
    return send_from_directory(os.path.join(FRONTEND_DIR, 'pages'), filename)

@app.route('/<path:path>', methods=['GET'])
def serve_static(path):
    # Don't intercept /api/* routes
    if path.startswith('api/'):
        return jsonify({"error": "Not found"}), 404
    file_path = os.path.join(FRONTEND_DIR, path)
    if os.path.isfile(file_path):
        return send_from_directory(FRONTEND_DIR, path)
    return send_from_directory(FRONTEND_DIR, 'index.html')


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
