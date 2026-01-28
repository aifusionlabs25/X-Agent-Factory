"""
Lead Scorer - Lightweight Rule-Based Scoring for G5.0
Assigns a quality score (1-10) to prospects based on available signals from Places Scout.
"""
from typing import Dict, List, Any

class LeadScorer:
    """
    Scoring logic for prospects.
    """
    
    def score_prospect(self, prospect: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate score for a prospect.
        Returns a dict with 'score', 'score_reason', and 'score_breakdown'.
        """
        score = 5 # Base score
        breakdown = ["Base Score: 5"]
        
        # 1. Website Signals
        # places_scout puts website in expanded_urls list, or sometimes just 'website' field if normalized differently
        website = prospect.get('website') or (prospect.get('expanded_urls') and prospect['expanded_urls'][0])
        domain_quality = prospect.get('domain_quality', 'low')
        
        if website:
            score += 2
            breakdown.append("Has Website: +2")
            
            if domain_quality == 'good':
                score += 1
                breakdown.append("Good Domain: +1")
        else:
            score -= 2
            breakdown.append("No Website: -2")
            
        # 2. B2B Confidence (if available)
        b2b_conf = prospect.get('b2b_confidence', 0)
        if b2b_conf > 7:
            score += 2
            breakdown.append(f"High B2B Confidence ({b2b_conf}): +2")
        elif b2b_conf > 0 and b2b_conf < 4:
            score -= 1
            breakdown.append(f"Low B2B Confidence ({b2b_conf}): -1")
            
        # 3. Contact Info & GBP Data
        gbp = prospect.get('gbp_data', {})
        if gbp.get('phone'):
            score += 1
            breakdown.append("Has Phone: +1")
        else:
            score -= 1
            breakdown.append("No Phone: -1")
            
        # 4. Social Proof (Ratings)
        try:
            rating = float(gbp.get('rating', 0))
            user_ratings_total = int(gbp.get('userRatingCount', 0))
            
            if user_ratings_total == 0 and 'user_ratings_total' in gbp:
                 user_ratings_total = int(gbp.get('user_ratings_total', 0))

            if rating >= 4.5:
                score += 1
                breakdown.append(f"High Rating ({rating}): +1")
            elif rating < 3.5 and rating > 0:
                score -= 1
                breakdown.append(f"Low Rating ({rating}): -1")
                
            if user_ratings_total > 50:
                score += 1
                breakdown.append(f"High Review Count ({user_ratings_total}): +1")
        except:
            pass
            
        # 5. Industry/Keywords (from tags/types)
        tags = prospect.get('tags', [])
        # Example positive keywords
        if any(t in tags for t in ['plumber', 'lawyer', 'dentist', 'hvac', 'contractor']):
            # slightly boost known high-value verticals
            score += 1
            breakdown.append("High Value Vertical: +1")

        # Clamp Score 1-10
        score = max(1, min(10, score))
        
        return {
            "score": score,
            "score_reason": ", ".join(breakdown),
            "score_breakdown": breakdown,
            "confidence": self._calculate_confidence(prospect)
        }

    def _calculate_confidence(self, prospect: Dict) -> str:
        """
        Calculate confidence (low/medium/high) based on data completeness.
        """
        checks = 0
        if prospect.get('website'): checks += 1
        if prospect.get('phone') or prospect.get('gbp_data', {}).get('phone'): checks += 1
        if prospect.get('name'): checks += 1
        
        # Address?
        if prospect.get('formatted_address'): checks += 1
        
        if checks >= 3:
            return "high"
        elif checks == 2:
            return "medium"
        return "low"

def get_scorer() -> LeadScorer:
    return LeadScorer()
