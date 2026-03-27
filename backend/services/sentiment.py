"""
Sentiment Analysis + Priority Mapping
"""


def map_sentiment_to_priority(sentiment: str, current_priority: str = 'medium') -> str:
    """Map sentiment to a minimum priority level."""
    priority_levels = {'low': 0, 'medium': 1, 'high': 2, 'critical': 3}
    current_level = priority_levels.get(current_priority, 1)

    sentiment_min = {
        'happy': 0,      # low
        'neutral': 1,    # medium
        'frustrated': 2, # high
        'angry': 3       # critical
    }

    min_level = sentiment_min.get(sentiment, 1)
    final_level = max(current_level, min_level)

    for name, level in priority_levels.items():
        if level == final_level:
            return name
    return current_priority


def check_auto_escalation(ticket: dict, new_message: str) -> dict:
    """
    Returns: { should_escalate: bool, reason: str }
    """
    # Rule 1: Angry sentiment on high-priority open ticket
    if ticket.get('sentiment') == 'angry' and ticket.get('priority') in ['high', 'critical']:
        return {"should_escalate": True, "reason": "Customer expressing anger on critical issue"}

    # Rule 2: Duplicate escalation protection (< 24 hours)
    if ticket.get('last_escalated_at'):
        from datetime import datetime, timezone, timedelta
        try:
            last_esc = datetime.fromisoformat(ticket['last_escalated_at'].replace('Z', '+00:00'))
            if datetime.now(timezone.utc) - last_esc < timedelta(hours=24):
                return {"should_escalate": False, "reason": "Already escalated within 24 hours"}
        except Exception:
            pass

    # Rule 3: Repeated complaint keyword detection
    complaint_keywords = [
        'still not resolved', 'again', 'same issue', 'third time',
        'unacceptable', 'terrible', 'worst experience', 'never again',
        'lawyer', 'legal action', 'report', 'scam'
    ]
    if any(kw in new_message.lower() for kw in complaint_keywords):
        return {"should_escalate": True, "reason": "Customer indicates repeated/unresolved issue"}

    return {"should_escalate": False, "reason": None}
