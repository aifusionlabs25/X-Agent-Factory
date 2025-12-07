# Phase 3: Deployment & UI - Implementation Plan

## Goal Description
Deploy the generated agent ("Ava") to the Tavus platform and build the "Factory Dashboard" which serves as both the management console and the "Agent-First" interactive demo environment.

## User Review Required
> [!IMPORTANT]
> **Tavus Integration**: I will be using the `TAVUS_API_KEY` from `.env.local`. Ensure this key has permissions to create Personas/Replicas.

## Proposed Changes

### Tools
#### [NEW] `tools/deploy_agent.py`
- **Purpose**: Uploads the generated `system_prompt.txt` and identity to Tavus to create a live conversational replica.
- **Platform**: Tavus API (Phoenix/V2).

### Dashboard (The "Factory Floor")
#### [NEW] `dashboard/` (Next.js Application)
- **Stack**: Next.js 14 (App Router), Tailwind CSS.
- **Key Features**:
    1.  **Agent Grid**: View all generated agents (e.g., Ava).
    2.  **Interactive Demo Mode**:
        - **Layout**: Fixed Right Sidebar (`w-[500px]`) for the Agent Video.
        - **Main Area**: Dynamic Iframe (Client Website).
        - **Mechanism**: Iframe scaling (0.55x) as defined in Protocol.

### Workflows
#### [NEW] `.agent/workflows/deploy-agent.md`
- Workflow to run the deployment script.

## Verification Plan

### Automated Tests
- `python tools/deploy_agent.py --test` (Mocked deployment to verify logic).

### Manual Verification
1.  Run deployment for "Ava".
2.  Launch Dashboard (`npm run dev`).
3.  Verify "Agent-First" Layout renders correctly with the sidebar.
4.  Test Iframe scaling mechanism.
