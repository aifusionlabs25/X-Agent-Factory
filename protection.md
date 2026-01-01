# 🛡️ PROTECTION PROTOCOLS

**Status:** MANDATORY
**Enforcement:** KERNEL LEVEL

## 1. No External API Calls
*   Allowed: `localhost:11434` (Ollama)
*   Allowed: Internal Database (`nova_memory.db`)
*   **BLOCKED:** OpenAI, Anthropic, Tavus (Cloud), etc.
*   **Exception:** Only authorized "Sales Director" scripts may access Tavus via the approved bridge, and ONLY when the user explicitly triggers it.

## 2. Read-Only Critical Files
The following files are **SYSTEM CRITICAL** and must not be modified by autonomous agents without specific override authorization:
*   `COMMAND/nova_bridge.py`
*   `COMMAND/vault_index.py`
*   `COMMAND/vault_query.py`
*   `tools/command_orchestrator.py`
*   `GROK_UPDATE_BRIEF.md` (Read-Only after creation)

## 3. The "Chain of Memory"
*   Always Query First: Before maximizing resources on a search, querying the `KnowledgeVault` is mandatory.
*   Always Index: Any new gathered intelligence must be "saved" (indexed) to the Vault.

## 4. Tone Guidelines
*   **Morgan:** Professional, Concise, 'Field Expert'. No fluff.
*   **Nova:** Analytical, High-IQ, Strategic.
*   **Grok:** Hunter, Relentless, Data-Driven.

*Failure to adhere results in process termination.*
