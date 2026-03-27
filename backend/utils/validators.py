"""
Input Validators
"""


def validate_email(email: str) -> bool:
    """Basic email validation."""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_priority(priority: str) -> bool:
    return priority in ('low', 'medium', 'high', 'critical')


def validate_status(status: str) -> bool:
    return status in ('open', 'in_progress', 'escalated', 'closed')


def validate_sentiment(sentiment: str) -> bool:
    return sentiment in ('happy', 'neutral', 'frustrated', 'angry')


def validate_role(role: str) -> bool:
    return role in ('customer', 'attendee', 'admin')


def sanitize_string(text: str, max_length: int = 1000) -> str:
    """Trim and limit string length."""
    if not text:
        return ''
    return text.strip()[:max_length]
