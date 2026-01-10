import sqlite3
import json
import os
from pathlib import Path
from datetime import datetime

# DB Path: intelligence/factory.db
DB_PATH = Path(__file__).parent.parent / "intelligence" / "factory.db"
SCHEMA_PATH = Path(__file__).parent / "db_schema.sql"

def init_db():
    """Initialize the database with the schema."""
    if not DB_PATH.parent.exists():
        DB_PATH.parent.mkdir(parents=True)
        
    conn = sqlite3.connect(DB_PATH)
    with open(SCHEMA_PATH, 'r') as f:
        schema = f.read()
    conn.executescript(schema)
    conn.close()
    print(f"   🗄️  Database initialized: {DB_PATH}")

def get_connection():
    """Get a connection to the database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row # Allow assessing columns by name
    return conn

def upsert_lead(lead_data):
    """
    Insert or Update a lead.
    Matches on URL.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Prepare data (handle JSON fields)
    contact_json = json.dumps(lead_data.get('contact', {}), ensure_ascii=False)
    email_json = json.dumps(lead_data.get('email_draft', {}), ensure_ascii=False)
    sales_intel_json = json.dumps(lead_data.get('sales_intel', {}), ensure_ascii=False)
    
    # Check if exists
    url = lead_data.get('href', '')
    if not url:
        return # Skip leads without URL
        
    try:
        cursor.execute("""
            INSERT INTO leads (
                business_name, url, vertical, location, nova_score, nova_reason,
                priority, urgency, contact_data, email_draft, sales_intel, source_file
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(url) DO UPDATE SET
                business_name=excluded.business_name,
                vertical=excluded.vertical,
                nova_score=excluded.nova_score,
                nova_reason=excluded.nova_reason,
                priority=excluded.priority,
                urgency=excluded.urgency,
                contact_data=excluded.contact_data,
                email_draft=excluded.email_draft,
                sales_intel=excluded.sales_intel,
                updated_at=CURRENT_TIMESTAMP
        """, (
            lead_data.get('title', 'Unknown'),
            url,
            lead_data.get('vertical', ''),
            lead_data.get('location', ''),
            lead_data.get('nova_score', 0),
            lead_data.get('nova_reason', ''),
            lead_data.get('priority', 'C'),
            lead_data.get('urgency', 0),
            contact_json,
            email_json,
            sales_intel_json,
            lead_data.get('source_file', '')
        ))
        conn.commit()
    except Exception as e:
        print(f"   ⚠️ DB Error ({url}): {e}")
    finally:
        conn.close()

def get_leads(vertical=None, limit=100):
    """Retrieve leads, optionally filtered by vertical."""
    conn = get_connection()
    cursor = conn.cursor()
    
    if vertical:
        cursor.execute("SELECT * FROM leads WHERE vertical LIKE ? ORDER BY nova_score DESC LIMIT ?", (f"%{vertical}%", limit))
    else:
        cursor.execute("SELECT * FROM leads ORDER BY created_at DESC LIMIT ?", (limit,))
        
    rows = cursor.fetchall()
    conn.close()
    
    # Convert rows to dicts
    results = []
    for row in rows:
        results.append(dict(row))
    return results

if __name__ == "__main__":
    init_db()
    # Test
    # upsert_lead({"title": "Test Biz", "href": "http://example.com"})
