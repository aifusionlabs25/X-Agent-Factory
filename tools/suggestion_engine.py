from datetime import datetime, timedelta
from typing import Dict, List, Optional

class SuggestionEngine:
    """
    Generates rule-based suggestions for leads based on their state,
    activity, and enrichment data.
    """
    
    def generate_suggestions(self, lead: Dict, tasks: List[Dict] = []) -> List[Dict]:
        suggestions = []
        
        # 1. High Score + New -> Call
        if lead.get('score', 0) >= 8 and lead.get('status') == 'new':
            if lead.get('phone'):
                suggestions.append({
                    "action": "call",
                    "label": "Call Priority Lead",
                    "reason": "High Score (8+) and has Phone number.",
                    "confidence": "high"
                })
        
        # 2. Contacted + No Follow-up
        if lead.get('status') == 'contacted':
            has_future_task = any(
                t['status'] != 'done' and 
                datetime.fromisoformat(t['due_at']) > datetime.now() 
                for t in tasks
            )
            if not has_future_task:
                 suggestions.append({
                    "action": "follow_up",
                    "label": "Schedule Follow-up",
                    "reason": "Lead contacted but no future task scheduled.",
                    "confidence": "medium"
                })
                
        # 3. Verify Info
        if lead.get('score', 0) > 5 and not lead.get('phone') and not lead.get('website'):
             suggestions.append({
                "action": "verify",
                "label": "Verify Contact Info",
                "reason": "Good lead but missing contact details.",
                "confidence": "low"
            })
            
        return suggestions
