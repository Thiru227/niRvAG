"""
Voice Route — Upload voice resolution
"""
from flask import Blueprint, request, jsonify, g
from utils.auth_middleware import require_auth
from models.supabase_client import update_ticket, get_ticket_by_id, create_ticket_event
from services.email_service import send_email_notification
import datetime

voice_bp = Blueprint('voice', __name__)


@voice_bp.route('/upload', methods=['POST'])
@require_auth(roles=['admin', 'attendee'])
def upload_voice():
    if 'audio' not in request.files:
        return jsonify({"error": "No audio file provided"}), 400

    ticket_id = request.form.get('ticket_id')
    if not ticket_id:
        return jsonify({"error": "ticket_id is required"}), 400

    ticket = get_ticket_by_id(ticket_id)
    if not ticket:
        return jsonify({"error": "Ticket not found"}), 404

    audio_file = request.files['audio']

    # In production, upload to Supabase Storage
    # For now, save locally and store path
    import os
    import tempfile
    voice_dir = os.path.join(tempfile.gettempdir(), 'nirvag_voices')
    os.makedirs(voice_dir, exist_ok=True)
    filename = f"{ticket_id}_{datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')}.webm"
    filepath = os.path.join(voice_dir, filename)
    audio_file.save(filepath)

    # Update ticket
    update_ticket(ticket_id, {
        'status': 'closed',
        'resolution_voice_url': filepath,
        'resolution_text': f'[Voice resolution recorded by {g.user["name"]}]',
        'updated_at': datetime.datetime.utcnow().isoformat()
    })

    create_ticket_event({
        'ticket_id': ticket_id,
        'actor_email': g.user['email'],
        'event_type': 'resolved',
        'new_value': 'closed',
        'note': 'Resolved via voice note'
    })

    # Notify customer
    try:
        send_email_notification('ticket_resolved', {
            'to_email': ticket['user_email'],
            'name': ticket['user_name'],
            'number': ticket.get('ticket_number', ''),
            'title': ticket['title'],
            'resolution': 'Our agent has recorded a voice resolution for your issue.',
            'brand_name': 'niRvAG'
        })
    except Exception:
        pass

    return jsonify({"message": "Voice note uploaded and ticket resolved", "file": filename})
