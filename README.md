# 🏗️ X Agent Factory

**The Machine That Builds The Machine.**

The **X Agent Factory** is an industrial-grade system designed to automate the discovery, design, creation, and deployment of specialized AI agents. Unlike single-agent frameworks, the Factory focuses on **scalability**, **modularity**, and **vertical-specific intelligence**.

---

## 🧩 Core Architecture

The Factory operates via distinct "Specialist" modules, orchestrated to act as a cohesive production line:

### 1. 🔭 The Market Scout (R&D)
*   **Role**: Identifies high-value opportunities.
*   **Engine**: Scrapes pain points, calculates Total Addressable Market (TAM), and scores verticals.
*   **Output**: `intelligence/daily_opportunities.json`
*   **Code**: `tools/prospect_scout.py`

### 2. 🧬 The Persona Architect (Design)
*   **Role**: Designs the agent's brain.
*   **Engine**: Loads vertical templates (e.g., Veterinary, HVAC) and fills in specific business data to generate a robust system prompt.
*   **Output**: `agents/{agent_name}/system_prompt.txt`
*   **Code**: `tools/persona_architect.py`

### 3. 🏭 The Factory Orchestrator (Production)
*   **Role**: Manages the end-to-end pipeline from lead to outreach.
*   **Workflow**:
    1.  **Hunt**: `tools/prospect_scout.py` finds qualified leads.
    2.  **Enrich**: `tools/contact_enricher.py` finds decision-maker emails.
    3.  **Rank**: **Nova** (AI) ranks leads A/B/C.
    4.  **Draft**: **Sparkle** (AI) writes hyper-personalized emails.
    5.  **Report**: Generates Markdown & HTML reports + CSVs.

### 4. 📈 The Dashboard (Control Center)
*   **Role**: UI for managing the factory.
*   **Stack**: Next.js 14 + Tailwind CSS.
*   **Features**:
    *   **Growth Engine**: Visual interface for the Market Scout.
    *   **Interactive Demo**: "Agent-First" layout for client previews.
    *   **System Status**: Real-time monitoring of API usage (Gemini, Tavus, ElevenLabs).

---

## 📂 Repository Structure

```text
├── agents/                 # Generated agents & knowledge bases
├── dashboard/              # Next.js Control Panel application
├── intelligence/           # The Factory's "Brain" (Leads, Reports, Atlas)
│   ├── leads/              # Raw hunt results (JSON/CSV)
│   ├── reports/            # Orchestrator reports (Markdown)
│   └── market_atlas.json   # Database of scored verticals
├── specialists/            # System prompts for internal factory workers (Nova, Sparkle, etc.)
├── templates/              # Vertical-specific agent templates (JSON)
└── tools/                  # Python backend utilities & scripts
```

---

## 🚀 Key Workflows

### 1. Run a Market Hunt
Find leads for a specific niche (e.g., Veterinary Clinics in Phoenix).
```bash
# Via Dashboard: Go to /growth -> Select Vertical -> Click "HUNT"
# Via CLI:
python tools/prospect_scout.py "veterinary clinics in phoenix"
```

### 2. Orchestrate Outreach
Process leads, rank them, and generate email drafts.
```bash
# Auto-triggered by Dashboard or run manually:
python tools/factory_orchestrator.py --file intelligence/leads/veterinary_qualified.json
```

### 3. Deploy an Agent
Push a local agent configuration to the Tavus platform for a live replica.
```bash
python tools/deploy_agent.py --agent ava_veterinary
```

---

## 🛠️ Technology Stack

*   **Core Intelligence**: Google Gemini 1.5 Flash, Ollama (Llama 3 Local)
*   **Video/Voice**: Tavus (Phoenix API), ElevenLabs
*   **Frontend**: Next.js 14, React, Tailwind CSS
*   **Backend**: Python 3.10+, FastAPI (Orchestration Layer)

---

## 📝 License
Proprietary & Confidential. Property of **AI Fusion Labs**.
