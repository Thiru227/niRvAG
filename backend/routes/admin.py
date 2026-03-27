"""
Admin Routes
"""
from flask import Blueprint, request, jsonify, g
from utils.auth_middleware import require_auth
from models.supabase_client import (
    get_all_users, create_user as db_create_user, update_user as db_update_user,
    get_brand_settings, update_brand_settings,
    get_tickets, _get, _delete
)
import bcrypt

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/users', methods=['GET'])
@require_auth(roles=['admin'])
def list_users():
    users = get_all_users()
    return jsonify(users)


@admin_bp.route('/users', methods=['POST'])
@require_auth(roles=['admin'])
def create_user():
    data = request.get_json()
    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    role = data.get('role', 'attendee')

    if not name or not email or not password:
        return jsonify({"error": "Name, email, and password are required"}), 400

    if role not in ['attendee', 'admin']:
        return jsonify({"error": "Role must be attendee or admin"}), 400

    # Hash password
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    try:
        result = db_create_user({
            'name': name,
            'email': email,
            'password_hash': password_hash,
            'role': role,
            'expertise': data.get('expertise', ''),
            'description': data.get('description', ''),
            'is_active': True
        })

        return jsonify(result or {}), 201
    except Exception as e:
        return jsonify({"error": f"Failed to create user: {str(e)}"}), 400


@admin_bp.route('/users/<user_id>', methods=['PATCH'])
@require_auth(roles=['admin'])
def update_user(user_id):
    data = request.get_json()
    allowed = ['name', 'expertise', 'description', 'is_active', 'role']
    update_data = {k: v for k, v in data.items() if k in allowed}

    # Handle password reset
    if 'password' in data and data['password']:
        update_data['password_hash'] = bcrypt.hashpw(
            data['password'].encode('utf-8'), bcrypt.gensalt()
        ).decode('utf-8')

    result = db_update_user(user_id, update_data)
    return jsonify(result or {})


@admin_bp.route('/users/<user_id>', methods=['DELETE'])
@require_auth(roles=['admin'])
def delete_user(user_id):
    db_update_user(user_id, {'is_active': False})
    return jsonify({"message": "User deactivated"})


@admin_bp.route('/settings', methods=['GET'])
@require_auth(roles=['admin'])
def get_settings():
    settings = get_brand_settings()
    return jsonify(settings)


@admin_bp.route('/settings', methods=['POST'])
@require_auth(roles=['admin'])
def save_settings():
    data = request.get_json()
    allowed = ['brand_name', 'tone', 'welcome_message', 'color_primary', 'logo_url']
    update_data = {k: v for k, v in data.items() if k in allowed}
    update_brand_settings(update_data)
    return jsonify({"message": "Settings saved"})


@admin_bp.route('/products', methods=['GET'])
@require_auth(roles=['admin'])
def list_products():
    products = _get('products')
    return jsonify(products)


@admin_bp.route('/products/<product_id>', methods=['DELETE'])
@require_auth(roles=['admin'])
def delete_product(product_id):
    try:
        _delete('products', {'id': f'eq.{product_id}'})
        return jsonify({"message": "Product deleted"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@admin_bp.route('/documents', methods=['GET'])
@require_auth(roles=['admin'])
def list_documents():
    documents = _get('documents')
    return jsonify(documents)


@admin_bp.route('/documents/<doc_id>', methods=['DELETE'])
@require_auth(roles=['admin'])
def delete_document(doc_id):
    try:
        # Also remove chunks from ChromaDB
        try:
            from services.rag import delete_document_chunks
            delete_document_chunks(doc_id)
        except Exception:
            pass
        _delete('documents', {'id': f'eq.{doc_id}'})
        return jsonify({"message": "Document deleted"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@admin_bp.route('/analytics', methods=['GET'])
@require_auth(roles=['admin'])
def get_analytics():
    # Fetch all tickets
    tickets = _get('tickets', {'select': 'status,sentiment,intent,created_at'})

    total = len(tickets)
    status_counts = {'open': 0, 'in_progress': 0, 'escalated': 0, 'closed': 0}
    sentiment_counts = {'happy': 0, 'neutral': 0, 'frustrated': 0, 'angry': 0}
    intent_counts = {}

    for t in tickets:
        s = t.get('status', 'open')
        if s in status_counts:
            status_counts[s] += 1

        sent = t.get('sentiment', 'neutral')
        if sent in sentiment_counts:
            sentiment_counts[sent] += 1

        intent = t.get('intent', 'other')
        intent_counts[intent] = intent_counts.get(intent, 0) + 1

    # Sort intents
    top_intents = sorted(
        [{'intent': k, 'count': v} for k, v in intent_counts.items()],
        key=lambda x: x['count'],
        reverse=True
    )[:10]

    return jsonify({
        "total_tickets": total,
        "open": status_counts['open'],
        "in_progress": status_counts['in_progress'],
        "escalated": status_counts['escalated'],
        "closed": status_counts['closed'],
        "sentiment_breakdown": sentiment_counts,
        "top_intents": top_intents,
    })


@admin_bp.route('/teams', methods=['GET'])
@require_auth(roles=['admin'])
def get_teams():
    """Return available team categories for the frontend."""
    from services.routing import get_team_categories
    return jsonify(get_team_categories())


@admin_bp.route('/rag/stats', methods=['GET'])
@require_auth(roles=['admin'])
def rag_stats():
    """Return RAG collection stats for debugging."""
    try:
        from services.rag import get_collection_stats
        return jsonify(get_collection_stats())
    except Exception as e:
        return jsonify({"available": False, "error": str(e)})
