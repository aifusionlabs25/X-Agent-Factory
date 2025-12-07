# Phase 4: System Integration - Implementation Plan

## Goal Description
Connect the "Factory Floor" (Dashboard UI) to the "Machine Arms" (Python Tools). We will turn the static dashboard into a fully functional control center that triggers the Market Scout, Architect, and Deployment tools via API routes.

## Proposed Changes

### 1. API Layer (The Bridge)
Create Next.js Route Handlers (`dashboard/app/api/`) to execute Python scripts safely.
*   `dashboard/app/api/scout/route.ts`: Executes `tools/market_scout.py` and returns JSON.
*   `dashboard/app/api/architect/route.ts`: Executes `tools/kb_generator.py`.
*   `dashboard/app/api/deploy/route.ts`: Executes `tools/deploy_agent.py`.

### 2. Dashboard Integration
Update `dashboard/app/page.tsx` to:
*   Fetch "Market Intelligence" from the live `intelligence/daily_opportunities.json` (via API).
*   Trigger "Deploy to Staging" button to actually call the deployment API.

### 3. Execution Flow
1.  **User** clicks "Deploy" on Dashboard.
2.  **Next.js API** spawns a Python subprocess.
3.  **Python Script** runs logic (Gemini/Tavus).
4.  **UI** updates with success/failure status.

## Verification
*   **Test**: Click "Deploy" on the dashboard.
*   **Verify**: Check that `deploy_agent.py` ran (logs) and a new replica was created in Tavus (if enabled) or mocked correctly.
