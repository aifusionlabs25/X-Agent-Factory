"""
Email Template Generator
Generates HTML email templates using Sparkle's copy.
Integrates with Morgan email infrastructure for sending.

STUB: Full implementation pending Morgan email system review.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import os
import json
from datetime import datetime

def load_specialist(name):
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'specialists', f'{name}.txt')
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    return ""

def generate_email_html(
    subject: str,
    body: str,
    recipient_name: str = "",
    sender_name: str = "The X Agent Factory Team",
    demo_link: str = "",
    company_name: str = ""
) -> str:
    """
    Generate a professional HTML email template.
    
    Args:
        subject: Email subject line
        body: Email body text (can include line breaks)
        recipient_name: Name of recipient
        sender_name: Name of sender
        demo_link: Optional demo link to include
        company_name: Company name for personalization
    
    Returns:
        Complete HTML email string
    """
    
    # Convert body line breaks to HTML
    body_html = body.replace('\n', '<br>')
    
    # Build CTA button if demo link provided
    cta_button = ""
    if demo_link:
        cta_button = f'''
        <tr>
            <td style="padding: 20px 0;">
                <a href="{demo_link}" style="
                    display: inline-block;
                    background: linear-gradient(135deg, #3B82F6 0%, #8B5CF6 100%);
                    color: #ffffff;
                    padding: 14px 32px;
                    text-decoration: none;
                    border-radius: 8px;
                    font-weight: bold;
                    font-size: 16px;
                ">🚀 See Your Custom Demo</a>
            </td>
        </tr>
        '''
    
    html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{subject}</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f4f4f7; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color: #f4f4f7;">
        <tr>
            <td align="center" style="padding: 40px 20px;">
                <table role="presentation" width="600" cellspacing="0" cellpadding="0" style="background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                    <!-- Header -->
                    <tr>
                        <td style="padding: 30px 40px; background: linear-gradient(135deg, #1e293b 0%, #334155 100%); border-radius: 12px 12px 0 0;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 24px;">🏗️ X Agent Factory</h1>
                        </td>
                    </tr>
                    
                    <!-- Body -->
                    <tr>
                        <td style="padding: 40px;">
                            {f'<p style="margin: 0 0 20px; color: #374151; font-size: 16px;">Hi {recipient_name},</p>' if recipient_name else ''}
                            
                            <p style="margin: 0 0 20px; color: #374151; font-size: 16px; line-height: 1.6;">
                                {body_html}
                            </p>
                        </td>
                    </tr>
                    
                    <!-- CTA -->
                    {cta_button}
                    
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 30px 40px; background-color: #f8fafc; border-radius: 0 0 12px 12px; text-align: center;">
                            <p style="margin: 0 0 10px; color: #64748b; font-size: 14px;">
                                {sender_name}
                            </p>
                            <p style="margin: 0; color: #94a3b8; font-size: 12px;">
                                Powered by AI Fusion Labs | X Agent Factory
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>'''
    
    return html


def generate_outreach_email(
    lead_name: str,
    lead_domain: str,
    pain_point: str,
    demo_link: str,
    sparkle_subject: str = "",
    sparkle_body: str = ""
) -> dict:
    """
    Generate a complete outreach email for a lead.
    
    If sparkle_subject/body not provided, generates default copy.
    
    Returns:
        {
            "subject": str,
            "body_text": str,
            "body_html": str,
            "recipient_domain": str
        }
    """
    
    # Use provided or generate default
    subject = sparkle_subject or f"A quick thought about {lead_name}'s phone lines"
    
    body = sparkle_body or f"""I noticed {lead_name} might be dealing with {pain_point.lower()}.

We built a custom AI demo specifically for your business. It took us about 30 seconds to see the opportunity.

Would you be open to a 5-minute look?"""
    
    html = generate_email_html(
        subject=subject,
        body=body,
        recipient_name="",
        sender_name="The X Agent Factory Team",
        demo_link=demo_link,
        company_name=lead_name
    )
    
    return {
        "subject": subject,
        "body_text": body,
        "body_html": html,
        "recipient_domain": lead_domain,
        "demo_link": demo_link,
        "generated_at": datetime.now().isoformat()
    }


def save_email_template(email_data: dict, slug: str) -> str:
    """Save generated email to templates directory."""
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'intelligence', 'emails')
    os.makedirs(output_dir, exist_ok=True)
    
    # Save HTML version
    html_path = os.path.join(output_dir, f"{slug}_email.html")
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(email_data['body_html'])
    
    # Save metadata
    meta_path = os.path.join(output_dir, f"{slug}_email.json")
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump({
            "subject": email_data['subject'],
            "body_text": email_data['body_text'],
            "recipient_domain": email_data['recipient_domain'],
            "demo_link": email_data['demo_link'],
            "generated_at": email_data['generated_at']
        }, f, indent=2)
    
    print(f"✅ Email template saved to: {html_path}")
    return html_path


if __name__ == "__main__":
    # Test email generation
    email = generate_outreach_email(
        lead_name="Desert Diamond Air",
        lead_domain="desertdiamondair.com",
        pain_point="After-hours calls going to voicemail",
        demo_link="https://factory.aifusionlabs.com/demo/desert_diamond_air"
    )
    
    print("Subject:", email['subject'])
    print("\nBody (Text):")
    print(email['body_text'])
    print("\n✅ HTML email generated")
    
    # Save template
    save_email_template(email, "desert_diamond_air")
