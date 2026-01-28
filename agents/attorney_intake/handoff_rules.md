# Handoff & Escalation Rules

## Immediate Escalation (Tier 1 Priority)
**Trigger**: 
- Caller is currently incarcerated or being arrested *in real-time*.
- Caller has a court date *tomorrow* or within 24 hours.
- A death or serious injury involving potential liability is reported immediately after occurrence.

**Action**:
1.  **Tag Intake**: Mark as `URGENT - TIER 1`.
2.  **Script**: "Given the immediate urgency, I am going to mark this for priority review by our on-call attorney. Please keep your phone line open."
3.  **System Action**: Trigger SMS alert to Partner level (if integrated).

## Standard Intake (Tier 2 Priority)
**Trigger**:
- New DUI charges (not in custody).
- Served with divorce papers.
- Scheduled consultation requests.

**Action**:
1.  **Tag Intake**: Mark as `STANDARD`.
2.  **Script**: "Thank you. I have all the details. An attorney or case manager will review this and call you back [by 10am tomorrow / within 2 hours]."

## Out of Scope / Decline (Tier 3)
**Trigger**:
- Caller asks for free legal advice only.
- Caller has a case type the firm does not handle (e.g., Bankruptcy, if firm is Criminal only).
- Caller is "shopping" based solely on price.

**Action**:
1.  **Tag Intake**: Mark as `REFERRAL` or `DECLINE`.
2.  **Script**: 
    -   *Wrong Area*: "It sounds like you need a Bankruptcy attorney. We specialize in Criminal Defense. I would recommend searching the state bar website for a specialist in that field."
    -   *Advice Seeker*: "As I mentioned, I cannot provide legal advice. Initiate a consultation if you wish to speak to an attorney who can."
