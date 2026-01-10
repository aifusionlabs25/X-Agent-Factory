CREATE TABLE IF NOT EXISTS leads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_name TEXT NOT NULL,
    url TEXT UNIQUE,
    vertical TEXT,
    location TEXT,
    nova_score INTEGER,
    nova_reason TEXT,
    priority TEXT,           -- A, B, C
    urgency INTEGER,        -- 1-10
    status TEXT DEFAULT 'new',
    contact_data TEXT,       -- JSON: {email, phone, name...}
    email_draft TEXT,        -- JSON: {subject, body...}
    sales_intel TEXT,        -- JSON: {pain_points, hooks...}
    source_file TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
