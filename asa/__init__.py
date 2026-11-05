"""asa - Agent Surface Audit.

Black-box behavioural audit of PayPal's agent surface (the official Agent
Toolkit and MCP server) measured against the sandbox, followed by bounded
exploit-sequence search over the measured behaviour model and a policy-DSL
compile / repair loop with the LLM.

Ground rules carried from the ideation blueprint (E5/E6/G6):
  * sandbox only - the config guard refuses anything else,
  * probe first, never enforce - measurement, not runtime guarding,
  * every call leaves a JSONL receipt; no claim without a receipt,
  * the deterministic checker decides, not the LLM.
"""

__version__ = "0.1.0+scaffold"
