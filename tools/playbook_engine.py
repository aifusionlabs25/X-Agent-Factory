"""
Playbook Engine - G7.0 (Operator Excellence)
Generates the "Next Best Action" for a lead based on available signals.
"""
from typing import Dict, List, Optional
import datetime

def generate_playbook(lead: Dict) -> Dict:
    """
    Generate a recommendation JSON for a lead.
    
    Inputs (expected in lead dict):
    - score (float/int)
    - phone (str/None)
    - website (str/None)
    - rating (float)
    - status (str)
    """
    score = lead.get('score', 0) or 0  # Handle None
    has_phone = bool(lead.get('phone'))
    has_website = bool(lead.get('website'))
    rating = lead.get('rating', 0) or 0
    status = lead.get('status', 'new')
    
    action = "Review"
    reason = "Standard review needed."
    script = ""
    channel = "Manual"
    priority = "Normal"
    
    # Logic Rules
    if status == 'new':
        if score >= 8:
            priority = "High"
            if has_phone:
                action = "Call Now"
                channel = "Phone"
                reason = "High value lead with phone. prioritize direct contact."
                script = "Hi, this is [Name]. I saw your high rating on Google..."
            elif has_website:
                action = "Visit Website / Form"
                channel = "Web"
                reason = "good lead but no phone. Try contact form."
            else:
                action = "Manual Research"
                reason = "High score but low contact info. Verify existence."
                
        elif score >= 5:
            priority = "Normal"
            if has_phone and rating < 4.0:
                action = "Call (Reputation)"
                channel = "Phone"
                reason = "Decent score, but low rating. Pitch reputation management."
            elif has_website:
                action = "Email / LinkedIn"
                channel = "Email"
                reason = "Standard outreach."
            else:
                action = "Skip / Low Priority"
                reason = "Mid score without contact info."
                
        else: # Score < 5
            action = "Archive / Watchlist"
            priority = "Low"
            reason = "Low score. Keep for future or bulk outreach."
            
    elif status == 'contacted':
        action = "Follow Up"
        reason = "Lead contacted. Check for reply or schedule next touch."
        
    return {
        "action": action,
        "reason": reason,
        "channel": channel,
        "priority": priority,
        "script": script,
        "generated_at": datetime.datetime.now().isoformat()
    }
