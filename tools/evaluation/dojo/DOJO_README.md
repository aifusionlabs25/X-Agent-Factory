# DOJO EVALUATION SUITE (Bolt-on)

**Location**: `tools/evaluation/dojo/`
**Status**: READ-ONLY / SHADOW MODE

## Components
1.  **Loader** (`dojo_agent_loader.py`): Maps Factory agents to Dojo format.
2.  **Runner** (`dojo_runner.py`): Runs simulations vs Scenarios (`scenarios/`).
3.  **Scorer** (`dojo_scorer.py`): Grades transcripts (Legal/SDR rubrics).
4.  **Coach** (`dojo_coach.py`): Analyzes failures -> Shadow Orders (`shadow_orders/`).
5.  **Architect** (`dojo_architect.py`): Fixes Prompts -> Patches (`patches/`).

## Usage

### 1. Run Simulation
```bash
python tools/evaluation/dojo/dojo_runner.py <client_slug> <scenario_path>
```
*Output: `dojo_logs/<client_slug>/<timestamp>_<scenario>.txt`*

### 2. Score Transcript
```bash
python tools/evaluation/dojo/dojo_scorer.py <log_path> --rubric [legal|sdr]
```
*Output: `...score.json`*

### 3. Diagnose Failure (Shadow Coach)
```bash
python tools/evaluation/dojo/dojo_coach.py <log_path>
```
*Output: `shadow_orders/<client_slug>/CO_....json`*

### 4. Draft Patch (Shadow Architect)
```bash
python tools/evaluation/dojo/dojo_architect.py <order_path>
```
*Output: `shadow_orders/<client_slug>/patches/....patch`*

## G15.2 Adherence Checking
The Scorer implements "Observable Adherence" for Reasoning Modes:
*   **Legal Intake**: Checks for Issue Framing + Advice Denial.
*   **SDR**: Checks for Pattern Interrupt + Value Prop.
