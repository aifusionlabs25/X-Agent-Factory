# X Agent Factory — Vision Module

**Status:** Experimental (Phase 1)
**Purpose:** Visual perception capabilities for X Agents

---

## Structure

```
modules/vision/
├── data/               ← Training images (labeled)
├── models/             ← Trained model checkpoints
├── api/                ← FastAPI deployment code
├── notebooks/          ← Jupyter experiments
└── README.md           ← This file
```

---

## Quick Start

1. **Data Collection:** Use WebWorker to scrape images
2. **Labeling:** GPT-4V assisted or manual labeling
3. **Training:** Roboflow or HuggingFace (local 5080)
4. **Deployment:** FastAPI endpoint
5. **Integration:** Tavus perception_tool webhook

---

## Current Focus: Veterinary Triage

**Goal:** Visual observation assistant (NOT diagnostic)

**Detects:**
- Pet in frame (dog/cat/other)
- Visible symptoms (redness, swelling, discharge)
- Behavior cues (lethargy, limping)

**Always includes:**
- Confidence score
- Disclaimer about AI limitations
- Recommendation to consult a vet

---

## Legal Positioning

> **This module provides observational suggestions only.**
> It is NOT medical advice and NOT a substitute for 
> a licensed veterinarian examination.

---

## Related Docs

- [Vision Module Deep Analysis](file:///C:/Users/AI%20Fusion%20Labs/.gemini/antigravity/brain/876a27b0-4e41-4d3d-89c3-c9281d57d075/VISION_MODULE_DEEP_ANALYSIS.md)
- [Tavus Perception Reference](file:///C:/Users/AI%20Fusion%20Labs/.gemini/antigravity/brain/876a27b0-4e41-4d3d-89c3-c9281d57d075/TAVUS_PERCEPTION_REFERENCE.md)
