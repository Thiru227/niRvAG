"""
Attendee Routes (placeholder — tickets are shared via tickets.py)
"""
from flask import Blueprint

attendee_bp = Blueprint('attendee', __name__)

# Attendee-specific routes are handled via the tickets blueprint.
# This blueprint exists for future attendee-only features.
