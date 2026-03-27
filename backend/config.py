import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'nirvag-dev-secret')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    
    # Supabase
    SUPABASE_URL = os.getenv('SUPABASE_URL', '')
    SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY', '')
    SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY', '')
    
    # Claude
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')
    
    # Email
    SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
    SMTP_USER = os.getenv('SMTP_USER', '')
    SMTP_PASS = os.getenv('SMTP_PASS', '')
    FROM_EMAIL = os.getenv('FROM_EMAIL', 'support@nirvag.com')
    
    # CORS
    CORS_ORIGIN = os.getenv('CORS_ORIGIN', 'http://localhost:5500')
    
    # Optional
    ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY', '')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
