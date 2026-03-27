"""
Chat Route — POST /api/chat
Now with: email-based session carryover, ticket management, order ownership
"""
from flask import Blueprint, request, jsonify
from models.supabase_client import (
    create_chat_session, get_chat_session, update_chat_messages,
    get_chat_session_by_email,
    create_ticket, create_ticket_event, get_user_by_id, get_tickets_by_email
)
from services.ai_engine import process_chat
from services.routing import assign_ticket_to_attendee
from services.email_service import send_email_notification
import datetime

chat_bp = Blueprint('chat', __name__)


@chat_bp.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    message = data.get('message', '').strip()
    session_id = data.get('session_id')
    user_name = data.get('user_name', 'Customer')
    user_email = data.get('user_email', '')

    if not message:
        return jsonify({"error": "Message is required"}), 400

    # Get or create session — carry over context from previous sessions by email
    if session_id:
        session = get_chat_session(session_id)
        if not session:
            # Try to find previous session by email for context carryover
            if user_email:
                prev_session = get_chat_session_by_email(user_email)
                session = create_chat_session(user_email, user_name)
                # Carry over previous messages as context
                if prev_session and session:
                    prev_msgs = prev_session.get('messages', []) or []
                    if isinstance(prev_msgs, str):
                        import json as _json
                        try:
                            prev_msgs = _json.loads(prev_msgs)
                        except Exception:
                            prev_msgs = []
                    if prev_msgs:
                        update_chat_messages(session['id'], prev_msgs)
                        session['messages'] = prev_msgs
            else:
                session = create_chat_session(user_email, user_name)
    else:
        # First message — check if returning customer by email
        if user_email:
            prev_session = get_chat_session_by_email(user_email)
            session = create_chat_session(user_email, user_name)
            # Carry over previous messages as context
            if prev_session and session:
                prev_msgs = prev_session.get('messages', []) or []
                if isinstance(prev_msgs, str):
                    import json as _json
                    try:
                        prev_msgs = _json.loads(prev_msgs)
                    except Exception:
                        prev_msgs = []
                if prev_msgs:
                    # Keep last 20 messages from previous sessions as context
                    carried_msgs = prev_msgs[-20:]
                    update_chat_messages(session['id'], carried_msgs)
                    session['messages'] = carried_msgs
        else:
            session = create_chat_session(user_email, user_name)

    if not session:
        return jsonify({"error": "Failed to create chat session"}), 500

    session_id = session['id']
    chat_history = session.get('messages', []) or []

    # Ensure chat_history is a list
    if isinstance(chat_history, str):
        import json as _json
        try:
            chat_history = _json.loads(chat_history)
        except Exception:
            chat_history = []
    if not isinstance(chat_history, list):
        chat_history = []

    # Process through AI engine
    try:
        ai_result = process_chat(message, {
            'user_name': user_name,
            'user_email': user_email
        }, chat_history)
    except Exception as e:
        print(f"AI Engine Error: {e}")
        ai_result = {
            'response': "I apologize, but I'm having trouble processing your request right now. Please try again in a moment.",
            'intent': 'other',
            'sentiment': 'neutral',
            'priority': 'medium',
            'action': 'none',
            'ticket_title': None,
            'ticket_description': None
        }

    # Update chat history
    now = datetime.datetime.utcnow().isoformat()
    chat_history.append({"role": "user", "content": message, "timestamp": now})
    chat_history.append({"role": "assistant", "content": ai_result.get('response', ''), "timestamp": now})
    update_chat_messages(session_id, chat_history)

    # Handle ticket creation
    ticket_created = False
    ticket_info = None

    if ai_result.get('action') == 'create_ticket':
        try:
            ticket_data = {
                'user_name': user_name,
                'user_email': user_email,
                'title': ai_result.get('ticket_title', 'Support Request'),
                'description': ai_result.get('ticket_description', message),
                'priority': ai_result.get('priority', 'medium'),
                'status': 'open',
                'sentiment': ai_result.get('sentiment', 'neutral'),
                'intent': ai_result.get('intent', 'other'),
            }

            ticket = create_ticket(ticket_data)

            if ticket:
                ticket_created = True

                # Create event
                create_ticket_event({
                    'ticket_id': ticket['id'],
                    'actor_email': user_email,
                    'event_type': 'created',
                    'new_value': 'open',
                    'note': f'Auto-created by AI from chat'
                })

                # Smart routing — assign to best attendee
                try:
                    assignment = assign_ticket_to_attendee(
                        ticket_data['description'],
                        ticket_data['intent']
                    )
                    if assignment and assignment.get('assigned_id'):
                        from models.supabase_client import update_ticket
                        update_ticket(ticket['id'], {'assigned_to': assignment['assigned_id']})
                        assigned_user = get_user_by_id(assignment['assigned_id'])
                        ticket['assigned_to_name'] = assigned_user['name'] if assigned_user else None

                        create_ticket_event({
                            'ticket_id': ticket['id'],
                            'actor_email': 'system',
                            'event_type': 'assigned',
                            'new_value': assigned_user['name'] if assigned_user else assignment['assigned_id'],
                            'note': assignment.get('reason', 'AI routing')
                        })

                        # Notify attendee
                        try:
                            send_email_notification('ticket_assigned_agent', {
                                'to_email': assigned_user['email'],
                                'name': assigned_user['name'],
                                'number': ticket.get('ticket_number', ''),
                                'title': ticket_data['title'],
                                'priority': ticket_data['priority'],
                                'brand_name': 'niRvAG'
                            })
                        except Exception:
                            pass
                except Exception as e:
                    print(f"Routing error: {e}")

                ticket_info = {
                    'id': ticket['id'],
                    'ticket_number': ticket.get('ticket_number'),
                    'status': ticket.get('status', 'open'),
                    'priority': ticket.get('priority', 'medium'),
                    'title': ticket_data['title'],
                    'assigned_to_name': ticket.get('assigned_to_name')
                }

                # Send ticket created email to customer
                try:
                    send_email_notification('ticket_created', {
                        'to_email': user_email,
                        'name': user_name,
                        'number': ticket.get('ticket_number', ''),
                        'title': ticket_data['title'],
                        'priority': ticket_data['priority'],
                        'assigned_to': ticket.get('assigned_to_name', 'Our team'),
                        'brand_name': 'niRvAG'
                    })
                except Exception:
                    pass

        except Exception as e:
            print(f"Ticket creation error: {e}")

    # Handle ticket escalation
    if ai_result.get('action') == 'escalate_ticket':
        try:
            # Find ticket to escalate from description
            desc = ai_result.get('ticket_description', '')
            tickets = get_tickets_by_email(user_email)
            target_ticket = None
            
            # Try to match ticket number from description or message
            import re
            ticket_num_match = re.search(r'#?(\d+)', desc + ' ' + message)
            if ticket_num_match and tickets:
                num = ticket_num_match.group(1)
                for t in tickets:
                    if str(t.get('ticket_number', '')) == num:
                        target_ticket = t
                        break
            
            # If no specific match, escalate the most recent open ticket
            if not target_ticket and tickets:
                for t in tickets:
                    if t.get('status') in ['open', 'in_progress']:
                        target_ticket = t
                        break

            if target_ticket:
                from models.supabase_client import update_ticket
                update_ticket(target_ticket['id'], {
                    'status': 'escalated',
                    'priority': 'critical',
                    'updated_at': datetime.datetime.utcnow().isoformat()
                })
                create_ticket_event({
                    'ticket_id': target_ticket['id'],
                    'actor_email': user_email,
                    'event_type': 'escalated',
                    'new_value': 'escalated',
                    'note': f'Escalated by customer via chat: {message}'
                })
                try:
                    send_email_notification('ticket_escalated', {
                        'to_email': user_email,
                        'name': user_name,
                        'number': target_ticket.get('ticket_number', ''),
                        'title': target_ticket.get('title', ''),
                        'brand_name': 'niRvAG'
                    })
                except Exception:
                    pass
        except Exception as e:
            print(f"Escalation error: {e}")

    return jsonify({
        "reply": ai_result.get('response', ''),
        "session_id": session_id,
        "ticket_created": ticket_created,
        "ticket": ticket_info,
        "sentiment": ai_result.get('sentiment', 'neutral'),
        "intent": ai_result.get('intent', 'other')
    })
