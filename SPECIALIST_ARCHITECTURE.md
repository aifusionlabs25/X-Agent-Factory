# SPECIALIST ARCHITECTURE (The Orchestrator)

## Overview
Phase 9 moves the Factory from a single-llm logic to a "Specialist Roster" approach. Instead of generic prompts, we use defined Personas with distinct contexts to execute specific stages of the Agent Generation Loop.

## The Roster

### 1. WebWorker (The Eyes) -> `market_scout.py`
- **Role**: Deep Web Analysis & Market Research.
- **Context**: Expert in crawling, parsing, and identifying high-value signal vs noise.
- **Output**: Detailed Opportunity JSON with sources.

### 2. Troy (The Builder) -> `persona_architect.py`
- **Role**: Agent Architecture & System Prompt Design.
- **Context**: Senior Systems Engineer. Obsessed with structure, safeguards, and specialized protocols.
- **Output**: `system_prompt.txt` (Structured, bulletproof).

### 3. Sparkle (The Voice) -> `marketing_generator.py`
- **Role**: Copywriting & Sales Psychology.
- **Context**: World-class marketer. Knows how to write emails that convert.
- **Output**: Sales Sequences, Landing Page Copy.

### 4. Fin (The Ledger) -> `dashboard/app/billing`
- **Role**: Revenue Optimization.
- **Context**: CFO / Pricing Strategist.
- **Output**: Pricing models, Tier definitions.

### 5. Nova (The Vision) -> `factory_orchestrator.py`
- **Role**: Product Visionary.
- **Context**: Tie breaking, strategic direction.
- **Output**: Roadmap, feature prioritization.

## Integration Pattern
Each tool in `tools/` will now load its specific `specialists/{Name}.txt` context file before executing its logic.
