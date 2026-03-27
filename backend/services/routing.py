"""
Smart Routing — Team-based + LLM-assisted ticket assignment
"""
import json
from config import Config

try:
    from models.supabase_client import get_active_attendees
except ImportError:
    def get_active_attendees():
        return []


# ── Team Categories for routing ──
TEAM_CATEGORIES = {
    'order_shipping': {
        'name': 'Order & Shipping',
        'keywords': ['order', 'shipping', 'delivery', 'tracking', 'shipped', 'transit',
                     'package', 'dispatch', 'courier', 'delayed', 'lost'],
        'intents': ['order_status', 'shipping']
    },
    'billing_payments': {
        'name': 'Billing & Payments',
        'keywords': ['payment', 'refund', 'billing', 'invoice', 'charge', 'money',
                     'transaction', 'receipt', 'credit', 'debit', 'upi', 'wallet'],
        'intents': ['refund_request', 'billing']
    },
    'technical_support': {
        'name': 'Technical Support',
        'keywords': ['bug', 'error', 'crash', 'broken', 'not working', 'technical',
                     'glitch', 'issue', 'problem', 'fail', 'login', 'password', 'account'],
        'intents': ['technical', 'complaint']
    },
    'product_inquiries': {
        'name': 'Product Inquiries',
        'keywords': ['product', 'feature', 'catalog', 'recommendation', 'size', 'color',
                     'specification', 'compare', 'model', 'warranty', 'return policy'],
        'intents': ['product_inquiry']
    },
    'general_support': {
        'name': 'General Support',
        'keywords': ['help', 'support', 'question', 'info', 'general', 'other', 'feedback'],
        'intents': ['general', 'other']
    }
}


def _match_team(description: str, intent: str) -> str:
    """Match ticket to a team category based on keywords and intent."""
    description_lower = description.lower()
    intent_lower = intent.lower() if intent else ''

    scores = {}
    for team_key, team in TEAM_CATEGORIES.items():
        score = 0

        # Check intent match (high weight)
        if intent_lower in team['intents']:
            score += 10

        # Check keyword matches in description
        for keyword in team['keywords']:
            if keyword in description_lower:
                score += 2

        scores[team_key] = score

    # Return team with highest score, default to general_support
    best_team = max(scores, key=scores.get)
    if scores[best_team] == 0:
        return 'general_support'
    return best_team


def assign_ticket_to_attendee(ticket_description: str, intent: str) -> dict | None:
    """
    Route ticket to the best agent using:
    1. Team-based keyword matching (fast, deterministic)
    2. LLM fallback if multiple agents share the same team
    """

    attendees = get_active_attendees()
    if not attendees:
        return None

    # If only one attendee, assign directly
    if len(attendees) == 1:
        return {
            "assigned_id": attendees[0]['id'],
            "reason": "Only available agent"
        }

    # Step 1: Match ticket to a team category
    matched_team = _match_team(ticket_description, intent)
    team_name = TEAM_CATEGORIES[matched_team]['name']

    # Step 2: Find agents whose expertise matches the team
    team_agents = []
    for agent in attendees:
        expertise = (agent.get('expertise') or '').lower()
        # Check if any of the team keywords appear in agent expertise
        for keyword in TEAM_CATEGORIES[matched_team]['keywords'][:5]:
            if keyword in expertise:
                team_agents.append(agent)
                break

    # If we found team-matched agents, pick the first one (or use LLM for fine-tuning)
    if team_agents:
        if len(team_agents) == 1:
            return {
                "assigned_id": team_agents[0]['id'],
                "reason": f"Matched to {team_name} team — {team_agents[0]['name']}"
            }
        # Multiple agents on same team — use LLM to pick best
        candidates = team_agents
    else:
        # No team match — fall back to all agents
        candidates = attendees

    # Step 3: LLM-assisted fine routing (if API key available)
    if not Config.ANTHROPIC_API_KEY:
        return {
            "assigned_id": candidates[0]['id'],
            "reason": f"Routed to {team_name} team (default)"
        }

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)

        attendee_list = "\n".join([
            f"- ID: {a['id']} | Name: {a['name']} | Expertise: {a.get('expertise', 'general')} | Bio: {a.get('description', 'Support agent')}"
            for a in candidates
        ])

        prompt = f"""
        Given this support ticket:
        Intent: {intent}
        Matched Team: {team_name}
        Description: {ticket_description}

        Available agents on this team:
        {attendee_list}

        Return ONLY a JSON object:
        {{"assigned_id": "uuid-here", "reason": "brief reason"}}

        Pick the agent whose expertise and bio best matches the ticket issue.
        If no clear match, pick the one with most general expertise.
        """

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}]
        )

        raw = response.content[0].text
        import re
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            result = json.loads(match.group())
            # Validate the assigned_id exists
            valid_ids = [a['id'] for a in candidates]
            if result.get('assigned_id') in valid_ids:
                result['reason'] = f"{team_name}: {result.get('reason', 'AI routing')}"
                return result

        return {
            "assigned_id": candidates[0]['id'],
            "reason": f"Routed to {team_name} team (default)"
        }

    except Exception as e:
        print(f"Routing LLM error: {e}")
        return {
            "assigned_id": candidates[0]['id'],
            "reason": f"Routed to {team_name} team (fallback)"
        }


def get_team_categories():
    """Return team categories for frontend display."""
    return {key: cat['name'] for key, cat in TEAM_CATEGORIES.items()}
