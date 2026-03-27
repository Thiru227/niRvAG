"""
Ticket Routes — CRUD
"""
from flask import Blueprint, request, jsonify, g
from utils.auth_middleware import require_auth
from models.supabase_client import (
    get_tickets, get_ticket_by_id, create_ticket, update_ticket,
    create_ticket_event, get_ticket_events, get_user_by_id
)
from services.email_service import send_email_notification
import datetime

tickets_bp = Blueprint('tickets', __name__)


@tickets_bp.route('/tickets', methods=['GET'])
@require_auth(roles=['admin', 'attendee'])
def list_tickets():
    status = request.args.get('status', '')
    priority = request.args.get('priority', '')
    mine = request.args.get('mine', '')

    filters = {}
    if status and ',' not in status:
        filters['status'] = status
    if priority:
        filters['priority'] = priority
    if mine == 'true' and g.user.get('role') == 'attendee':
        filters['assigned_to'] = g.user['id']

    tickets = get_tickets(filters)

    # If status has commas, filter in-memory
    if status and ',' in status:
        allowed = [s.strip() for s in status.split(',')]
        tickets = [t for t in tickets if t.get('status') in allowed]

    # Enrich with assigned_to name
    for t in tickets:
        if t.get('assigned_to'):
            user = get_user_by_id(t['assigned_to'])
            t['assigned_to_name'] = user['name'] if user else None
        else:
            t['assigned_to_name'] = None

    return jsonify(tickets)


@tickets_bp.route('/tickets/<ticket_id>', methods=['GET'])
@require_auth(roles=['admin', 'attendee'])
def get_single_ticket(ticket_id):
    ticket = get_ticket_by_id(ticket_id)
    if not ticket:
        return jsonify({"error": "Ticket not found"}), 404

    if ticket.get('assigned_to'):
        user = get_user_by_id(ticket['assigned_to'])
        ticket['assigned_to_name'] = user['name'] if user else None

    return jsonify(ticket)


@tickets_bp.route('/tickets', methods=['POST'])
@require_auth(roles=['admin', 'attendee'])
def create_ticket_route():
    data = request.get_json()
    required = ['user_name', 'user_email', 'title', 'description']
    for field in required:
        if not data.get(field):
            return jsonify({"error": f"{field} is required"}), 400

    ticket = create_ticket({
        'user_name': data['user_name'],
        'user_email': data['user_email'],
        'title': data['title'],
        'description': data['description'],
        'priority': data.get('priority', 'medium'),
        'status': 'open',
        'sentiment': data.get('sentiment', 'neutral'),
        'intent': data.get('intent', 'other'),
        'assigned_to': data.get('assigned_to'),
    })

    if ticket:
        create_ticket_event({
            'ticket_id': ticket['id'],
            'actor_email': g.user['email'],
            'event_type': 'created',
            'new_value': 'open',
            'note': 'Manually created'
        })

    return jsonify(ticket), 201


@tickets_bp.route('/tickets/<ticket_id>', methods=['PATCH'])
@require_auth(roles=['admin', 'attendee'])
def update_ticket_route(ticket_id):
    data = request.get_json()
    old_ticket = get_ticket_by_id(ticket_id)
    if not old_ticket:
        return jsonify({"error": "Ticket not found"}), 404

    allowed_fields = ['status', 'priority', 'assigned_to', 'sentiment']
    update_data = {k: v for k, v in data.items() if k in allowed_fields}
    update_data['updated_at'] = datetime.datetime.utcnow().isoformat()

    updated = update_ticket(ticket_id, update_data)

    # Log events
    for field in allowed_fields:
        if field in data and data[field] != old_ticket.get(field):
            event_type = 'status_change' if field == 'status' else 'priority_change' if field == 'priority' else 'assigned'
            create_ticket_event({
                'ticket_id': ticket_id,
                'actor_email': g.user['email'],
                'event_type': event_type,
                'old_value': str(old_ticket.get(field, '')),
                'new_value': str(data[field]),
            })

    return jsonify(updated)


@tickets_bp.route('/tickets/<ticket_id>/resolve', methods=['POST'])
@require_auth(roles=['admin', 'attendee'])
def resolve_ticket(ticket_id):
    data = request.get_json()
    resolution_text = data.get('resolution_text', '')

    if not resolution_text:
        return jsonify({"error": "Resolution text is required"}), 400

    updated = update_ticket(ticket_id, {
        'status': 'closed',
        'resolution_text': resolution_text,
        'updated_at': datetime.datetime.utcnow().isoformat()
    })

    create_ticket_event({
        'ticket_id': ticket_id,
        'actor_email': g.user['email'],
        'event_type': 'resolved',
        'new_value': 'closed',
        'note': resolution_text[:200]
    })

    # Send resolution email to customer
    ticket = get_ticket_by_id(ticket_id)
    if ticket:
        try:
            send_email_notification('ticket_resolved', {
                'to_email': ticket['user_email'],
                'name': ticket['user_name'],
                'number': ticket.get('ticket_number', ''),
                'title': ticket['title'],
                'resolution': resolution_text,
                'brand_name': 'niRvAG'
            })
        except Exception:
            pass

    return jsonify(updated)


@tickets_bp.route('/tickets/<ticket_id>/escalate', methods=['POST'])
@require_auth(roles=['admin', 'attendee'])
def escalate_ticket(ticket_id):
    data = request.get_json()
    reason = data.get('reason', '')

    if not reason:
        return jsonify({"error": "Escalation reason is required"}), 400

    updated = update_ticket(ticket_id, {
        'status': 'escalated',
        'escalation_reason': reason,
        'last_escalated_at': datetime.datetime.utcnow().isoformat(),
        'updated_at': datetime.datetime.utcnow().isoformat()
    })

    create_ticket_event({
        'ticket_id': ticket_id,
        'actor_email': g.user['email'],
        'event_type': 'escalated',
        'new_value': 'escalated',
        'note': reason
    })

    # Send escalation email to customer
    ticket = get_ticket_by_id(ticket_id)
    if ticket:
        try:
            send_email_notification('ticket_escalated', {
                'to_email': ticket['user_email'],
                'name': ticket['user_name'],
                'number': ticket.get('ticket_number', ''),
                'title': ticket.get('title', 'Support Request'),
                'brand_name': 'niRvAG'
            })
        except Exception:
            pass

    return jsonify(updated)


@tickets_bp.route('/tickets/<ticket_id>/events', methods=['GET'])
@require_auth(roles=['admin', 'attendee'])
def list_ticket_events(ticket_id):
    events = get_ticket_events(ticket_id)
    return jsonify(events)
