"""
AI Engine — Claude-powered chat with order lookup + RAG + product catalog
Now with: email-scoped orders, ticket context, chat history carryover
"""
import json
import os
import re
from config import Config


def load_demo_context():
    """Load FAQ + company info as baseline context."""
    ctx = ""
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
    for fname in ['faq.txt', 'company_info.txt']:
        path = os.path.join(data_dir, fname)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                ctx += f"\n\n--- {fname} ---\n" + f.read()
    return ctx


def lookup_order(message: str, user_email: str) -> tuple:
    """Check if message references an order ID and return order details.
    Returns (order_info_text, is_own_order) tuple.
    """
    orders_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'orders.json')
    if not os.path.exists(orders_file):
        return "", True

    try:
        with open(orders_file, 'r') as f:
            orders = json.load(f).get('orders', [])
    except Exception:
        return "", True

    # Extract order ID from message (e.g. ORD-1234, #1234, order 1234)
    order_match = re.search(r'(?:ORD-?|#|order\s*)(\d{3,6})', message, re.IGNORECASE)

    if order_match:
        oid_num = order_match.group(1)
        for o in orders:
            if oid_num in o['order_id']:
                # Check ownership — order must belong to this email
                if user_email and o['customer_email'].lower() != user_email.lower():
                    return f"ORDER_NOT_YOURS:{o['order_id']}", False
                return _format_order(o), True

    # Also show orders by email (own orders only)
    if user_email:
        own_orders = [o for o in orders if o['customer_email'].lower() == user_email.lower()]
        if own_orders:
            info = "\n\n--- YOUR ORDERS ---\n"
            for o in own_orders:
                info += _format_order(o)
            return info, True

    return "", True


def _format_order(o):
    """Format a single order into readable text."""
    info = f"""
Order ID: {o['order_id']}
Customer: {o['customer_name']}
Items: {', '.join([f"{i['name']} x{i['qty']}" for i in o['items']])}
Total: ${o['total']}
Status: {o['status'].upper()}
Payment: {o['payment_method']}
Tracking: {o.get('tracking_id', 'Not yet assigned')}
Ordered: {o.get('ordered_at', 'N/A')}
"""
    if o['status'] == 'delayed':
        info += f"Delay Reason: {o.get('delay_reason', 'N/A')}\nNew ETA: {o.get('new_estimated_delivery', 'N/A')}\n"
    elif o['status'] == 'cancelled':
        info += f"Refund Status: {o.get('refund_status', 'N/A')}\nRefund Amount: ${o.get('refund_amount', 0)}\n"
    elif o.get('estimated_delivery'):
        info += f"Estimated Delivery: {o['estimated_delivery']}\n"
    if o.get('delivered_at'):
        info += f"Delivered: {o['delivered_at']}\n"
    return info


def get_ticket_context(user_email: str) -> str:
    """Get all tickets for this customer to provide context."""
    try:
        from models.supabase_client import get_tickets_by_email
        tickets = get_tickets_by_email(user_email)
        if not tickets:
            return ""
        
        ctx = "\n\n--- CUSTOMER'S TICKETS ---\n"
        for t in tickets[:10]:  # limit to 10 most recent
            ctx += f"Ticket #{t.get('ticket_number', 'N/A')} | "
            ctx += f"Status: {t.get('status', 'unknown').upper()} | "
            ctx += f"Priority: {t.get('priority', 'medium')} | "
            ctx += f"Title: {t.get('title', 'Untitled')}\n"
            if t.get('resolution_text'):
                ctx += f"  Resolution: {t['resolution_text']}\n"
            if t.get('description'):
                ctx += f"  Description: {t['description'][:200]}\n"
        return ctx
    except Exception as e:
        print(f"[AI] Ticket context error: {e}")
        return ""


def process_chat(message: str, user_context: dict, chat_history: list = None) -> dict:
    """Process a chat message through Claude AI with full context."""

    user_email = user_context.get('user_email', '')
    user_name = user_context.get('user_name', 'Customer')

    # Gather context sources
    demo_context = load_demo_context()

    # Order lookup with ownership check
    order_info, is_own_order = lookup_order(message, user_email)

    if not is_own_order and order_info.startswith("ORDER_NOT_YOURS:"):
        order_id = order_info.split(":")[1]
        return {
            'response': f"I'm sorry, but order **{order_id}** is not associated with your email address ({user_email}). "
                        f"For security, I can only show you orders linked to your account. "
                        f"If you believe this is your order, please make sure you're using the same email address you ordered with. 🔒",
            'intent': 'order_status',
            'sentiment': 'neutral',
            'priority': 'low',
            'action': 'none',
            'ticket_title': None,
            'ticket_description': None
        }

    # Ticket context for this customer
    ticket_context = get_ticket_context(user_email)

    # RAG retrieval
    rag_context = ""
    try:
        from services.rag import retrieve_context
        rag_context = retrieve_context(message)
        if rag_context and "No " not in rag_context:
            rag_context = f"\n\n--- KNOWLEDGE BASE ---\n{rag_context}"
    except ImportError:
        pass

    # Product catalog
    product_context = ""
    try:
        from models.supabase_client import get_products
        products = get_products(limit=10)
        if products:
            product_context = "\n\n--- PRODUCT CATALOG ---\n"
            for p in products:
                product_context += f"• {p['name']} ({p['category']}) — ${p['price']} — {p.get('description', '')}\n"
    except Exception:
        pass

    # Brand settings
    brand_name = 'niRvAG'
    tone = 'professional'
    try:
        from models.supabase_client import get_brand_settings
        settings = get_brand_settings()
        brand_name = settings.get('brand_name', 'niRvAG')
        tone = settings.get('tone', 'professional')
    except Exception:
        pass

    # Format conversation history — use more context (last 10 msgs)
    history_msgs = []
    if chat_history:
        for h in chat_history[-10:]:  # last 5 exchanges
            role = h.get('role', 'user')
            content = h.get('content', '')
            if role in ['user', 'assistant']:
                history_msgs.append({"role": role, "content": content})

    system_prompt = f"""You are an AI customer support assistant for {brand_name}.
Your tone is {tone}, empathetic, and helpful.
The customer you are talking to is: {user_name} ({user_email}).

CRITICAL SECURITY RULES:
1. ONLY show order information that belongs to this customer's email ({user_email}). If they ask about an order not linked to their email, politely say: "That order is not associated with your email address. For security, I can only share details of orders linked to your account."
2. The customer can ONLY see their own tickets. Never share data from other customers.

TICKET MANAGEMENT:
- The customer can ask about their existing tickets. Their ticket data is provided below.
- When they ask about a CLOSED/RESOLVED ticket, explain the resolution reason clearly and mention "A copy of the resolution was sent to your email as a reminder."
- If the customer wants to CREATE a new ticket, set action to "create_ticket".
- If they want to ESCALATE an existing ticket, set action to "escalate_ticket" and include the ticket number in ticket_description.
- When they ask about ticket status, look at the CUSTOMER'S TICKETS data below and respond with the actual status.

CHAT HISTORY:
- You have access to the customer's previous conversation history. Use it to maintain context.
- If the customer refers to something discussed previously, use that context naturally.
- Remember their name, issues, and preferences from past messages.

ORDER RULES:
- If order data is provided below, use the ACTUAL order details (status, tracking, delivery dates) in your response.
- Be specific with tracking IDs and dates.
- If a customer asks about an order that's not in their records, mention what orders they DO have.

TICKET CREATION:
- Create tickets for: refunds, complaints, broken items, escalations, unresolved issues
- Do NOT create tickets for simple FAQ questions

CONTEXT:
{demo_context}
{order_info if is_own_order else ''}
{ticket_context}
{rag_context}
{product_context}

RESPONSE FORMAT — You MUST respond with ONLY a valid JSON object:
{{
  "response": "Your helpful reply to the customer",
  "intent": "order_status|refund_request|product_inquiry|complaint|billing|shipping|technical|ticket_status|general|other",
  "sentiment": "happy|neutral|frustrated|angry",
  "priority": "low|medium|high|critical",
  "action": "none|create_ticket|escalate_ticket",
  "ticket_title": "Short descriptive title if action is create_ticket, else null",
  "ticket_description": "Detailed description if action is create_ticket. If escalate, include ticket number. Else null"
}}"""

    # Build messages
    messages = history_msgs + [{"role": "user", "content": message}]

    # Call Claude
    if not Config.ANTHROPIC_API_KEY:
        return _smart_response(message, order_info if is_own_order else "", user_email, ticket_context)

    # Quick connectivity check — do a real HTTPS test, not just TCP
    try:
        import httpx
        probe = httpx.head("https://api.anthropic.com/v1/messages", timeout=4.0,
                           headers={"x-api-key": Config.ANTHROPIC_API_KEY or "test"})
        # Any HTTP response means we can reach the API
    except Exception:
        print("[AI] Anthropic API unreachable — using smart fallback")
        return _smart_response(message, order_info if is_own_order else "", user_email, ticket_context)

    try:
        import anthropic
        client = anthropic.Anthropic(
            api_key=Config.ANTHROPIC_API_KEY,
            timeout=8.0,
        )

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=800,
            system=system_prompt,
            messages=messages
        )

        raw = response.content[0].text

        # Parse JSON from response
        json_match = re.search(r'\{[\s\S]*\}', raw)
        if json_match:
            result = json.loads(json_match.group())
            result.setdefault('response', "I'm here to help! Could you please provide more details?")
            result.setdefault('intent', 'other')
            result.setdefault('sentiment', 'neutral')
            result.setdefault('priority', 'medium')
            result.setdefault('action', 'none')
            result.setdefault('ticket_title', None)
            result.setdefault('ticket_description', None)
            return result

        return {
            'response': raw, 'intent': 'other', 'sentiment': 'neutral',
            'priority': 'medium', 'action': 'none',
            'ticket_title': None, 'ticket_description': None
        }

    except Exception as e:
        print(f"Claude API error (falling back to smart mode): {e}")
        return _smart_response(message, order_info if is_own_order else "", user_email, ticket_context)


def _smart_response(message: str, order_info: str = "", user_email: str = "", ticket_context: str = "") -> dict:
    """Comprehensive smart fallback for demo mode — handles all common support scenarios."""
    msg = message.lower()

    # ── Ticket Status Queries ──
    if any(w in msg for w in ['ticket', 'status', 'my ticket', 'update on', 'follow up']):
        if ticket_context:
            # Check if asking about a closed ticket
            if any(w in msg for w in ['closed', 'resolved', 'done']):
                return _r(f"Here's the status of your resolved tickets:\n\n{ticket_context.strip()}\n\n"
                          "Each resolution has been sent to your email as a reminder. "
                          "If you need further assistance on any of these, I can reopen a ticket for you.",
                          'ticket_status', 'neutral', 'low')
            return _r(f"Here are your current tickets:\n\n{ticket_context.strip()}\n\n"
                      "Would you like me to create a new ticket or get more details on any of these?",
                      'ticket_status', 'neutral', 'low')
        return _r("You don't have any tickets on record yet. Would you like me to create one for your issue?",
                  'ticket_status', 'neutral', 'low')

    # ── Escalate ──
    if any(w in msg for w in ['escalate', 'supervisor', 'manager', 'higher']):
        return _r("I understand you'd like to escalate this matter. I'm creating an escalation ticket right away. "
                  "A senior team member will review your case within 2 hours.",
                  'complaint', 'frustrated', 'high', 'create_ticket',
                  'Escalation Request',
                  f'Customer requesting escalation. Message: {message}')

    # ── Order & Shipping ──
    if any(w in msg for w in ['order', 'track', 'deliver', 'shipping', 'ship', 'package', 'arrived', 'dispatch']):
        if order_info:
            return _r(f"I've found your order information! Here are the details:\n\n{order_info.strip()}\n\nIs there anything else you'd like to know about your order?",
                      'order_status', 'neutral', 'medium')
        if any(w in msg for w in ['not arrived', "hasn't", 'has not', 'late', 'delayed', 'missing', 'lost', '5 days', 'days']):
            return _r("I'm sorry to hear your order hasn't arrived yet. I'm creating a priority ticket so our shipping team can investigate this right away. They'll track your package and update you within 24 hours.",
                      'shipping', 'frustrated', 'high', 'create_ticket', 'Delayed/Missing Order',
                      f'Customer reports delayed or missing delivery. Message: {message}')
        return _r("I'd be happy to help with your order! Could you provide your order number (e.g., ORD-1234) so I can look up the details for you?",
                  'order_status', 'neutral', 'medium')

    # ── Refund & Returns ──
    if any(w in msg for w in ['refund', 'money back', 'return', 'defective', 'broken', 'damaged']):
        return _r("I understand you'd like a refund. I'm creating a ticket for our billing team to process this right away. Our refund policy covers returns within 30 days of purchase. You'll receive a confirmation email shortly.",
                  'refund_request', 'frustrated', 'high', 'create_ticket', 'Refund/Return Request',
                  f'Customer requesting refund or return. Message: {message}')

    # ── Payment & Billing ──
    if any(w in msg for w in ['payment', 'pay', 'billing', 'invoice', 'charge', 'credit card', 'transaction']):
        if any(w in msg for w in ['method', 'accept', 'how to pay', 'options']):
            return _r("We accept the following payment methods:\n\n• 💳 Credit/Debit Cards (Visa, Mastercard, Amex)\n• 🏦 Net Banking\n• 📱 UPI (Google Pay, PhonePe, Paytm)\n• 💰 Cash on Delivery (COD)\n• 🎁 Gift Cards & Store Credit\n\nAll transactions are secured with 256-bit SSL encryption. Is there anything else I can help with?",
                      'billing', 'neutral', 'low')
        return _r("I can help with billing inquiries. Let me create a ticket for our billing team to review your concern.",
                  'billing', 'neutral', 'medium', 'create_ticket', 'Billing Inquiry',
                  f'Customer has a billing question. Message: {message}')

    # ── Technical Issues ──
    if any(w in msg for w in ['login', 'password', 'error', 'bug', 'crash', "can't access", 'cannot', 'not working', 'technical', 'account']):
        return _r("I'm sorry you're facing technical difficulties. I'm escalating this to our technical support team right away. In the meantime, try clearing your browser cache and cookies. We'll get this resolved for you!",
                  'technical', 'frustrated', 'high', 'create_ticket', 'Technical Issue',
                  f'Customer reporting technical problem. Message: {message}')

    # ── Angry / Complaint ──
    if any(w in msg for w in ['worst', 'terrible', 'awful', 'hate', 'angry', 'frustrated', 'unacceptable', 'disgusted', 'scam', 'horrible']):
        return _r("I sincerely apologize for your experience. This is absolutely not the standard we aim to provide. I'm escalating your concern as a high-priority ticket. A supervisor will personally reach out within 2 hours.",
                  'complaint', 'angry', 'critical', 'create_ticket', 'Customer Complaint — Urgent',
                  f'Customer expressing strong dissatisfaction. Urgent escalation needed. Message: {message}')

    # ── Product Inquiries ──
    if any(w in msg for w in ['product', 'item', 'recommend', 'feature', 'warranty', 'catalog', 'price', 'stock', 'available']):
        return _r("Great question! Here are some of our bestsellers:\n\n• 🎧 Wireless Earbuds Pro — $79.99\n• ⌚ Smart Watch X1 — $199.99\n• 👕 Organic Cotton T-Shirt — $29.99\n• 🎒 Premium Backpack — $89.99\n• 🧘 Yoga Mat Deluxe — $49.99\n\nWould you like more details about any specific product?",
                  'product_inquiry', 'neutral', 'low')

    # ── International Shipping ──
    if any(w in msg for w in ['international', 'abroad', 'overseas', 'country', 'worldwide']):
        return _r("Yes! We deliver internationally to 50+ countries. Shipping takes 7-14 business days:\n\n• 🇺🇸 North America: $9.99\n• 🇪🇺 Europe: $12.99\n• 🌏 Asia Pacific: $14.99\n\nFree international shipping on orders over $100!",
                  'shipping', 'neutral', 'low')

    # ── Greeting ──
    if any(w in msg for w in ['hello', 'hi', 'hey', 'good morning', 'good evening', 'thanks', 'thank you']):
        return _r("Hello! 👋 Welcome to niRvAG Support! I'm here to help you with:\n\n• 📦 Order tracking & shipping\n• 💳 Payments & refunds\n• 🔧 Technical issues\n• 📦 Product information\n• 🎫 Ticket status & escalation\n\nHow can I assist you today?",
                  'general', 'happy', 'low')

    # ── Default ──
    return _r("Thank you for reaching out! I'd be happy to help. Could you tell me more about your concern? I can assist with orders, products, returns, billing, technical issues, and ticket status.",
              'general', 'neutral', 'low')


def _r(response, intent, sentiment, priority, action='none', title=None, desc=None):
    """Helper to build a response dict."""
    return {
        'response': response, 'intent': intent, 'sentiment': sentiment,
        'priority': priority, 'action': action,
        'ticket_title': title, 'ticket_description': desc
    }
