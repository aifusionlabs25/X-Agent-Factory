# Reasoning Mode Selector

This guide helps operators select the correct **Reasoning Mode Stack** based on the agent's Primary Job.

## 1. The Core Modes
*Ref: modes_of_reasoning.md*

| Mode | Token Cost | Latency | Best For |
| :--- | :--- | :--- | :--- |
| **Reflex** | Low | Low | Greetings, FAQs, Simple Routing. |
| **Hermeneutic** | Medium | Medium | Understanding intent, reading between lines (SDR/Legal). |
| **Adversarial** | High | High | Stress testing, fraud detection, qualification defense. |
| **Legal** | High | High | Checking against statute or case viability. |
| **Compliance** | High | High | Checking against policy or ethical guidelines. |

## 2. Standard Stacks (Presets)

### A. SDR Qualification (Outbound)
*Goal: Get the meeting, don't get tricked, ensure qualified.*
*   **Primary Job**: `SDR_HUNT`
*   **Preset ID**: `sdr_hunter_v1`
*   **Stack**:
    1.  `hermeneutic` (Is this a real objection or a smokescreen?)
    2.  `adversarial` (Are they qualified or just polite?)
    3.  `reflex` (Close the loop).

### B. Legal Intake (Inbound)
*Goal: Screen for case viability, do not give legal advice.*
*   **Primary Job**: `LEGAL_INTAKE`
*   **Preset ID**: `legal_intake_v1`
*   **Stack**:
    1.  `hermeneutic` (What is the *actual* legal issue here?)
    2.  `legal` (Does this map to our practice area?)
    3.  `compliance` (Am I accidentally giving advice? STOP.)

### C. Customer Support (Triage)
*Goal: Solve or Route.*
*   **Primary Job**: `SUPPORT_TRIAGE`
*   **Preset ID**: `support_triage_v1`
*   **Stack**:
    1.  `hermeneutic` (Sentiment analysis - are they angry?)
    2.  `reflex` (Standard protocol response).

## 3. How to Configure
Add the `reasoning_profile` object to your `persona_profile.json`.

```json
"reasoning_profile": {
    "preset_id": "legal_intake_v1",
    "primary_job": "LEGAL_INTAKE",
    "mode_stack": ["hermeneutic", "legal", "compliance"],
    "artifacts_expected": ["referral_decision"],
    "failure_checks": ["premature_closure", "unauthorized_advice"]
}
```
