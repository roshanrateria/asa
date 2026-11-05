"""Spike 4 (2026-11-06): snapshot the MCP tool list + input schemas.

Transports:
  stdio (default): npx -y @paypal/mcp --tools=all  (needs Node 18+; on Windows
                   set ASA_MCP_STDIO_COMMAND=npx.cmd if bare npx will not spawn)
  --remote:        streamable HTTP at mcp.sandbox.paypal.com (bearer-header
                   auth attempt; UNVERIFIED until proven, fallback = stdio)

Writes runs/mcp_tools_snapshot_<transport>.json and prints the tool name list
(ground truth for the matrix TOOL_TARGETS pruning, E5).

PAYPAL_ACCESS_TOKEN env var must hold a sandbox token (mint with the curl
snippet in README or let the REST spikes reuse their minted token manually).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from asa import mcp_client
from asa.config import load_config


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--remote", action="store_true",
                        help="use HTTP transport instead of stdio")
    args = parser.parse_args()

    cfg = load_config()
    transport = "http" if args.remote else "stdio"
    try:
        tools = mcp_client.snapshot_tools(cfg, transport=transport)
    except Exception as exc:  # noqa: BLE001 - spike script, report everything
        print(f"SPIKE4: FAIL ({transport}): {exc!r}")
        print("  Checklist: Node 18+ installed; PAYPAL_ACCESS_TOKEN set in .env;")
        print("  try ASA_MCP_STDIO_COMMAND=npx.cmd on Windows; retry --remote after stdio.")
        return 1

    out = Path(cfg.runs_dir) / f"mcp_tools_snapshot_{transport}.json"
    out.write_text(json.dumps({"transport": transport, "tools": tools}, indent=2),
                   encoding="utf-8")

    names = [t["name"] for t in tools]
    print(f"SPIKE4: PASS - {len(names)} tools via {transport}")
    for name in sorted(names):
        print(f"  {name}")
    print(f"snapshot: {out}")
    expected = {"create_invoice", "record_payment_for_invoice",
                "record_refund_for_invoice", "create_order", "pay_order",
                "create_refund", "get_invoice", "list_invoices"}
    missing = sorted(expected - set(names))
    print("matrix-relevant tools present:", "yes" if not missing else f"missing {missing}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
