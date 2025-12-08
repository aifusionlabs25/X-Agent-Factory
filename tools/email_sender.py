"""
Email Sender
Sends HTML email reports via Resend API.

Usage:
    from email_sender import send_hunt_report
    send_hunt_report("ceo@aifusionlabs.com", "Hunt Report", html_content)
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import os

# Resend SDK
try:
    import resend
except ImportError:
    print("⚠️ Resend not installed. Run: pip install resend")
    resend = None

from utils import load_env

def init_resend():
    """Initialize Resend with API key."""
    load_env()
    api_key = os.environ.get("RESEND_API_KEY")
    if not api_key:
        print("❌ RESEND_API_KEY not found in environment.")
        return False
    if resend:
        resend.api_key = api_key
        return True
    return False

def send_hunt_report(to_email: str, subject: str, html_content: str, from_name: str = "X Agent Factory"):
    """
    Sends an HTML email report via Resend.
    
    Args:
        to_email: Recipient email address
        subject: Email subject line
        html_content: Full HTML content
        from_name: Sender name (default: X Agent Factory)
    
    Returns:
        Response dict with 'id' on success, None on failure
    """
    if not init_resend():
        return None
    
    if not resend:
        print("❌ Resend SDK not available.")
        return None
    
    try:
        # Use Resend's test domain for now, or verified domain
        from_domain = os.environ.get("RESEND_FROM_DOMAIN", "onboarding@resend.dev")
        
        params = {
            "from": f"{from_name} <{from_domain}>",
            "to": [to_email],
            "subject": subject,
            "html": html_content
        }
        
        response = resend.Emails.send(params)
        print(f"✅ Email sent successfully!")
        print(f"   To: {to_email}")
        print(f"   Subject: {subject}")
        print(f"   Message ID: {response.get('id', 'N/A')}")
        return response
        
    except Exception as e:
        print(f"❌ Email failed: {e}")
        return None

def generate_report_html(vertical: str, leads: list, summary: dict) -> str:
    """
    Generate a beautiful HTML email report.
    
    Args:
        vertical: Hunt vertical name
        leads: List of qualified leads
        summary: Dict with total_leads, high_value, est_mrr
    
    Returns:
        Complete HTML string
    """
    # Build lead rows
    lead_rows = ""
    for lead in leads[:10]:  # Top 10
        score = lead.get('nova_score', 0)
        score_color = '#4ade80' if score >= 8 else '#facc15' if score >= 6 else '#f87171'
        demo_link = lead.get('demoLink', lead.get('demo_link', ''))
        
        lead_rows += f"""
        <tr>
            <td style="padding: 12px; border-bottom: 1px solid #333;">{lead.get('title', 'Unknown')[:40]}</td>
            <td style="padding: 12px; border-bottom: 1px solid #333; color: {score_color}; font-weight: bold;">{score}/10</td>
            <td style="padding: 12px; border-bottom: 1px solid #333;"><a href="{lead.get('href', '#')}" style="color: #60a5fa;">Visit</a></td>
            <td style="padding: 12px; border-bottom: 1px solid #333;">{f'<a href="{demo_link}" style="color: #4ade80;">Demo</a>' if demo_link else '—'}</td>
        </tr>
        """
    
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hunt Report: {vertical}</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; background: #0f172a; color: #e2e8f0;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background: #0f172a;">
        <tr>
            <td align="center" style="padding: 40px 20px;">
                <table role="presentation" width="600" cellspacing="0" cellpadding="0" style="background: #1e293b; border-radius: 16px; overflow: hidden; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5);">
                    
                    <!-- Header -->
                    <tr>
                        <td style="padding: 30px 40px; background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);">
                            <h1 style="margin: 0; color: white; font-size: 28px;">🎯 Hunt Report</h1>
                            <p style="margin: 8px 0 0; color: rgba(255,255,255,0.8); font-size: 16px;">{vertical}</p>
                        </td>
                    </tr>
                    
                    <!-- Stats Grid -->
                    <tr>
                        <td style="padding: 30px 40px;">
                            <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
                                <tr>
                                    <td width="33%" style="text-align: center; padding: 20px; background: #0f172a; border-radius: 12px;">
                                        <div style="font-size: 36px; font-weight: bold; color: #3b82f6;">{summary.get('total_leads', 0)}</div>
                                        <div style="color: #94a3b8; font-size: 14px; margin-top: 4px;">Total Leads</div>
                                    </td>
                                    <td width="10"></td>
                                    <td width="33%" style="text-align: center; padding: 20px; background: #0f172a; border-radius: 12px;">
                                        <div style="font-size: 36px; font-weight: bold; color: #4ade80;">{summary.get('high_value', 0)}</div>
                                        <div style="color: #94a3b8; font-size: 14px; margin-top: 4px;">High-Value (8+)</div>
                                    </td>
                                    <td width="10"></td>
                                    <td width="33%" style="text-align: center; padding: 20px; background: #0f172a; border-radius: 12px;">
                                        <div style="font-size: 36px; font-weight: bold; color: #fbbf24;">${summary.get('est_mrr', 0):,}</div>
                                        <div style="color: #94a3b8; font-size: 14px; margin-top: 4px;">Est. MRR</div>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Leads Table -->
                    <tr>
                        <td style="padding: 0 40px 30px;">
                            <h2 style="color: #f8fafc; font-size: 20px; margin: 0 0 20px;">🏆 Top Leads</h2>
                            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background: #0f172a; border-radius: 12px; overflow: hidden;">
                                <thead>
                                    <tr style="background: #334155;">
                                        <th style="padding: 12px; text-align: left; color: #94a3b8; font-weight: 600; font-size: 12px; text-transform: uppercase;">Business</th>
                                        <th style="padding: 12px; text-align: left; color: #94a3b8; font-weight: 600; font-size: 12px; text-transform: uppercase;">Score</th>
                                        <th style="padding: 12px; text-align: left; color: #94a3b8; font-weight: 600; font-size: 12px; text-transform: uppercase;">Website</th>
                                        <th style="padding: 12px; text-align: left; color: #94a3b8; font-weight: 600; font-size: 12px; text-transform: uppercase;">Demo</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {lead_rows if lead_rows else '<tr><td colspan="4" style="padding: 20px; text-align: center; color: #64748b;">No leads found</td></tr>'}
                                </tbody>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 30px 40px; background: #0f172a; text-align: center;">
                            <p style="margin: 0; color: #64748b; font-size: 14px;">
                                🏗️ X Agent Factory | Powered by AI Fusion Labs
                            </p>
                            <p style="margin: 10px 0 0; color: #475569; font-size: 12px;">
                                This is an automated hunt report. Reply to this email for support.
                            </p>
                        </td>
                    </tr>
                    
                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""

def send_batch_report(batch_name: str, vertical: str, leads: list, to_email: str = "aifusionlabs@gmail.com"):
    """
    Generate and send a complete batch report.
    
    Args:
        batch_name: e.g., "VET_BATCH_001"
        vertical: Hunt vertical name
        leads: List of qualified leads
        to_email: Recipient email
    
    Returns:
        Response from Resend API
    """
    # Calculate summary
    high_value = len([l for l in leads if l.get('nova_score', 0) >= 8])
    est_mrr = sum(2000 if l.get('nova_score', 0) >= 8 else 1000 if l.get('nova_score', 0) >= 6 else 500 for l in leads)
    
    summary = {
        'total_leads': len(leads),
        'high_value': high_value,
        'est_mrr': est_mrr
    }
    
    html = generate_report_html(vertical, leads, summary)
    subject = f"🎯 {batch_name}: {vertical} ({len(leads)} leads, ${est_mrr:,} MRR)"
    
    return send_hunt_report(to_email, subject, html)


if __name__ == "__main__":
    # Test with sample data
    test_leads = [
        {"title": "North Star Animal Hospital", "href": "https://northstaranimalhospital.com", "nova_score": 8},
        {"title": "Stony Brook Vet", "href": "https://stonybrookhomevet.com", "nova_score": 7},
    ]
    
    html = generate_report_html("Veterinary Clinics", test_leads, {
        'total_leads': 27,
        'high_value': 5,
        'est_mrr': 8000
    })
    
    # Save test HTML
    with open("test_email.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("✅ Test HTML saved to test_email.html")
    
    # Attempt send if API key exists
    if os.environ.get("RESEND_API_KEY"):
        send_batch_report("TEST_BATCH", "Veterinary", test_leads, "aifusionlabs@gmail.com")
    else:
        print("ℹ️ Set RESEND_API_KEY to enable email sending.")
