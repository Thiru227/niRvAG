-- ============================================
-- NIRVAH — Supabase Database Migration
-- Run this in Supabase SQL Editor
-- ============================================

-- 1. Users table
CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL,
  role TEXT NOT NULL DEFAULT 'customer' CHECK (role IN ('customer', 'attendee', 'admin')),
  password_hash TEXT,
  expertise TEXT,
  description TEXT,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Tickets table
CREATE TABLE IF NOT EXISTS tickets (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  ticket_number SERIAL UNIQUE,
  user_name TEXT NOT NULL,
  user_email TEXT NOT NULL,
  title TEXT NOT NULL,
  description TEXT NOT NULL,
  priority TEXT NOT NULL DEFAULT 'medium'
    CHECK (priority IN ('low', 'medium', 'high', 'critical')),
  status TEXT NOT NULL DEFAULT 'open'
    CHECK (status IN ('open', 'in_progress', 'escalated', 'closed')),
  sentiment TEXT DEFAULT 'neutral'
    CHECK (sentiment IN ('happy', 'neutral', 'frustrated', 'angry')),
  intent TEXT,
  assigned_to UUID REFERENCES users(id),
  resolution_text TEXT,
  resolution_voice_url TEXT,
  escalation_reason TEXT,
  last_escalated_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Chat Sessions table
CREATE TABLE IF NOT EXISTS chat_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_email TEXT NOT NULL,
  user_name TEXT NOT NULL,
  ticket_id UUID REFERENCES tickets(id),
  messages JSONB NOT NULL DEFAULT '[]',
  summary TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. Products table
CREATE TABLE IF NOT EXISTS products (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  category TEXT NOT NULL,
  price NUMERIC(10, 2) NOT NULL,
  description TEXT,
  stock_count INTEGER DEFAULT 0,
  is_available BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. Documents table
CREATE TABLE IF NOT EXISTS documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  filename TEXT NOT NULL,
  file_type TEXT NOT NULL,
  storage_path TEXT NOT NULL,
  chunk_count INTEGER DEFAULT 0,
  indexed_at TIMESTAMPTZ,
  uploaded_by UUID REFERENCES users(id),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 6. Ticket Events (Audit Log) table
CREATE TABLE IF NOT EXISTS ticket_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  ticket_id UUID REFERENCES tickets(id) ON DELETE CASCADE,
  actor_email TEXT NOT NULL,
  event_type TEXT NOT NULL,
  old_value TEXT,
  new_value TEXT,
  note TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 7. Chatbot Settings table
CREATE TABLE IF NOT EXISTS chatbot_settings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tone TEXT DEFAULT 'professional',
  brand_name TEXT DEFAULT 'Nirvah',
  welcome_message TEXT DEFAULT 'Hello! How can I help you today?',
  color_primary TEXT DEFAULT '#4F46E5',
  logo_url TEXT,
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- Indexes for performance
-- ============================================
CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status);
CREATE INDEX IF NOT EXISTS idx_tickets_priority ON tickets(priority);
CREATE INDEX IF NOT EXISTS idx_tickets_assigned_to ON tickets(assigned_to);
CREATE INDEX IF NOT EXISTS idx_tickets_created_at ON tickets(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_ticket_events_ticket ON ticket_events(ticket_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_email ON chat_sessions(user_email);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- ============================================
-- Enable Row Level Security
-- ============================================
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE tickets ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE products ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE ticket_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE chatbot_settings ENABLE ROW LEVEL SECURITY;

-- RLS Policies — Allow service role full access (backend uses service key)
CREATE POLICY "Service role full access" ON users FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service role full access" ON tickets FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service role full access" ON chat_sessions FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service role full access" ON products FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service role full access" ON documents FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service role full access" ON ticket_events FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service role full access" ON chatbot_settings FOR ALL USING (true) WITH CHECK (true);

-- ============================================
-- Seed: Default admin & agent accounts
-- Passwords: admin123, agent123 (bcrypt hashed)
-- ============================================
INSERT INTO users (name, email, role, password_hash, expertise, description, is_active)
VALUES
  ('Admin User', 'admin@nirvah.com', 'admin',
   '$2b$12$LJ3m4ys4Kzl8X9ZfN6E5/.FCqQnXM7WG0hJ0hY6YD/vKS5aWK176e',
   'administration', 'System administrator with full access', true),
  ('Ravi Kumar', 'agent@nirvah.com', 'attendee',
   '$2b$12$LJ3m4ys4Kzl8X9ZfN6E5/.FCqQnXM7WG0hJ0hY6YD/vKS5aWK176e',
   'payments, orders, shipping', 'Senior support agent specializing in order and payment issues', true),
  ('Priya Sharma', 'priya.agent@nirvah.com', 'attendee',
   '$2b$12$LJ3m4ys4Kzl8X9ZfN6E5/.FCqQnXM7WG0hJ0hY6YD/vKS5aWK176e',
   'technical, product, bugs', 'Technical support agent handling product issues and bugs', true)
ON CONFLICT (email) DO NOTHING;

-- Seed: Default chatbot settings
INSERT INTO chatbot_settings (brand_name, tone, welcome_message, color_primary)
VALUES ('Nirvah', 'professional', 'Hello! 👋 How can I help you today?', '#4F46E5')
ON CONFLICT DO NOTHING;

-- Seed: Sample products
INSERT INTO products (name, category, price, description, stock_count, is_available)
VALUES
  ('Wireless Earbuds Pro', 'Electronics', 79.99, 'Premium noise-cancelling wireless earbuds with 30hr battery life', 150, true),
  ('Smart Watch X1', 'Electronics', 199.99, 'Advanced smartwatch with health monitoring and GPS', 85, true),
  ('Organic Cotton T-Shirt', 'Clothing', 29.99, 'Soft organic cotton crew neck tee, available in 6 colors', 500, true),
  ('Premium Backpack', 'Accessories', 89.99, 'Water-resistant laptop backpack with USB charging port', 200, true),
  ('Yoga Mat Deluxe', 'Fitness', 49.99, 'Extra thick non-slip yoga mat with carrying strap', 300, true)
ON CONFLICT DO NOTHING;
