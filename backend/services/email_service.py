"""
Email Notification Service — Using Resend API
"""
import os
import json
from config import Config

try:
    import resend
    RESEND_AVAILABLE = True
except ImportError:
    RESEND_AVAILABLE = False

# Set Resend API key from env
RESEND_API_KEY = os.getenv('RESEND_API_KEY', '')
if RESEND_AVAILABLE and RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY

FROM_EMAIL_RAW = os.getenv('FROM_EMAIL', 'no-reply@nirvag.online')
FROM_EMAIL = f"niRvAG Support <{FROM_EMAIL_RAW}>"

TEMPLATES = {
    "ticket_created": {
        "subject": "Your support ticket #{number} has been created",
        "body": """
<div style="font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; max-width: 520px; margin: 0 auto; padding: 32px 24px; background: #fafafa; border-radius: 12px;">
  <div style="text-align: center; margin-bottom: 24px;">
    <div style="display: inline-block; width: 40px; height: 40px; background: #18181b; color: white; border-radius: 8px; line-height: 40px; font-weight: bold; font-size: 18px;">N</div>
  </div>
  <h2 style="margin: 0 0 8px; font-size: 20px; color: #18181b;">Ticket Created ✅</h2>
  <p style="color: #71717a; margin: 0 0 20px; font-size: 14px;">Hi {name}, we've received your support request.</p>
  <div style="background: white; border: 1px solid #e4e4e7; border-radius: 10px; padding: 16px; margin-bottom: 20px;">
    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
      <span style="color: #71717a; font-size: 13px;">Ticket</span>
      <span style="font-weight: 600; font-size: 13px;">#{number}</span>
    </div>
    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
      <span style="color: #71717a; font-size: 13px;">Issue</span>
      <span style="font-weight: 500; font-size: 13px;">{title}</span>
    </div>
    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
      <span style="color: #71717a; font-size: 13px;">Priority</span>
      <span style="font-weight: 600; font-size: 13px; text-transform: uppercase;">{priority}</span>
    </div>
    <div style="display: flex; justify-content: space-between;">
      <span style="color: #71717a; font-size: 13px;">Assigned</span>
      <span style="font-weight: 500; font-size: 13px;">{assigned_to}</span>
    </div>
  </div>
  <p style="color: #71717a; font-size: 13px; margin: 0;">Our team will get back to you shortly.<br>— {brand_name} Support</p>
</div>
"""
    },
    "ticket_resolved": {
        "subject": "✅ Ticket #{number} has been resolved",
        "body": """
<div style="font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; max-width: 520px; margin: 0 auto; padding: 32px 24px; background: #f0fdf4; border-radius: 12px;">
  <h2 style="margin: 0 0 8px; font-size: 20px; color: #18181b;">Ticket Resolved ✅</h2>
  <p style="color: #71717a; margin: 0 0 16px; font-size: 14px;">Hi {name}, your ticket #{number} has been resolved.</p>
  <div style="background: white; border: 1px solid #bbf7d0; border-radius: 10px; padding: 16px; margin-bottom: 16px;">
    <p style="margin: 0 0 8px; font-size: 13px; color: #71717a;">Issue: <strong>{title}</strong></p>
    <p style="margin: 0; font-size: 13px; color: #166534;"><strong>Resolution:</strong> {resolution}</p>
  </div>
  <p style="color: #71717a; font-size: 13px; margin: 0;">If you have further questions, reach out anytime.<br>— {brand_name} Support</p>
</div>
"""
    },
    "ticket_escalated": {
        "subject": "⚠️ Your ticket #{number} has been escalated",
        "body": """
<div style="font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; max-width: 520px; margin: 0 auto; padding: 32px 24px; background: #fffbeb; border-radius: 12px;">
  <h2 style="margin: 0 0 8px; font-size: 20px; color: #18181b;">Ticket Escalated ⚠️</h2>
  <p style="color: #71717a; margin: 0 0 16px; font-size: 14px;">Hi {name}, your ticket #{number} has been escalated to our senior team.</p>
  <p style="color: #71717a; font-size: 13px; margin: 0;">We understand the urgency and are prioritizing your request.<br>— {brand_name} Support</p>
</div>
"""
    },
    "ticket_assigned_agent": {
        "subject": "🎫 New ticket assigned: #{number} — {priority} priority",
        "body": """
<div style="font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; max-width: 520px; margin: 0 auto; padding: 32px 24px; background: #eff6ff; border-radius: 12px;">
  <h2 style="margin: 0 0 8px; font-size: 20px; color: #18181b;">New Ticket Assigned 🎫</h2>
  <p style="color: #71717a; margin: 0 0 16px; font-size: 14px;">Hi {name}, a new support ticket has been assigned to you.</p>
  <div style="background: white; border: 1px solid #bfdbfe; border-radius: 10px; padding: 16px; margin-bottom: 16px;">
    <p style="margin: 0 0 8px; font-size: 13px;"><strong>Ticket #{number}</strong></p>
    <p style="margin: 0 0 8px; font-size: 13px; color: #71717a;">Issue: {title}</p>
    <p style="margin: 0; font-size: 13px; color: #71717a;">Priority: <strong style="text-transform: uppercase;">{priority}</strong></p>
  </div>
  <p style="color: #71717a; font-size: 13px; margin: 0;">Please review and respond ASAP.<br>— {brand_name} System</p>
</div>
"""
    }
}


def send_email_notification(template_key: str, variables: dict):
    """Send an email notification using Resend API."""
    if not RESEND_AVAILABLE or not RESEND_API_KEY:
        print(f"[Email] Skipping — Resend not configured. Template: {template_key}, To: {variables.get('to_email', 'unknown')}")
        return False

    template = TEMPLATES.get(template_key)
    if not template:
        print(f"[Email] Unknown template: {template_key}")
        return False

    to_email = variables.get('to_email', '')
    if not to_email:
        print("[Email] No recipient email")
        return False

    try:
        subject = template["subject"].format(**variables)
        body = template["body"].format(**variables)
    except KeyError as e:
        print(f"[Email] Template variable missing: {e}")
        return False

    try:
        r = resend.Emails.send({
            "from": FROM_EMAIL,
            "to": to_email,
            "subject": subject,
            "html": body,
        })
        print(f"[Email] ✅ Sent '{template_key}' to {to_email} — ID: {r.get('id', 'unknown')}")
        return True
    except Exception as e:
        print(f"[Email] ❌ Failed to send: {e}")
        return False
