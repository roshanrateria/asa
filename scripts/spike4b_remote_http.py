"""Spike 4b (2026-11-06): remote MCP transports (/http + /sse) attempt.

Endpoint (docs): https://mcp.sandbox.paypal.com - transports /http and /sse;
auth either OAuth flow or a Bearer header. This spike tries the Bearer path
with a fresh sandbox token; every outcome (including silence) is a receipt,
closing unknown E (fallback documented: stdio is the verified transport).

On a successful /http initialize it attempts a tools/list to compare the
remote surface against the stdio snapshot (28 tools).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import httpx

from asa.config import load_config
from asa.recorder import Recorder
from asa.rest_client import RestClient

BASE = "https://mcp.sandbox.paypal.com"


def main() -> int:
    cfg = load_config()
    rec = Recorder(cfg.runs_dir, "spike4b-remote-http")
    token = RestClient(cfg, None)._token_fetch()
    rec.record(transport="mcp-http", tool="token",
               request={"note": "sandbox token fetched; secrets withheld"},
               response={"status": 200, "excerpt": f"access_token len={len(token)}"},
               cell="s4b-auth", notes="via client_credentials REST")

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json",
        "MCP-Protocol-Version": "2025-06-18",
    }
    init_body = {"jsonrpc": "2.0", "id": 1, "method": "initialize",
                 "params": {"protocolVersion": "2025-06-18",
                            "capabilities": {},
                            "clientInfo": {"name": "asa", "version": "0.0.1"}}}

    results = {}

    # -- streamable HTTP transport -------------------------------------------
    with httpx.Client(timeout=30.0) as http:
        try:
            r = http.post(f"{BASE}/http", json=init_body, headers=headers)
            session = r.headers.get("mcp-session-id")
            rec.record(transport="mcp-http", tool="initialize",
                       request={"jsonrpc": "initialize (secrets withheld)"},
                       response={"status": r.status_code,
                                 "excerpt": r.text[:400],
                                 "session_id": session,
                                 "echo_headers": {k: v for k, v in r.headers.items()
                                                  if k.lower().startswith("mcp")}},
                       cell="s4b-init", notes="POST " + BASE + "/http")
            results["http_initialize"] = r.status_code

            if r.status_code == 200 and session:
                r2 = http.post(f"{BASE}/http",
                               json={"jsonrpc": "2.0", "id": 2,
                                     "method": "tools/list"},
                               headers={**headers, "Mcp-Session-Id": session})
                rec.record(transport="mcp-http", tool="tools/list",
                           request={"jsonrpc": "tools/list"},
                           response={"status": r2.status_code,
                                     "excerpt": r2.text[:400]},
                           cell="s4b-tools", notes=f"session {session[:12]}...")
                results["http_tools_list"] = r2.status_code
                if r2.status_code == 200:
                    names = [t.get("name") for t in
                             (r2.json().get("result", {}).get("tools") or [])]
                    print(f"REMOTE TOOL COUNT: {len(names)}")
                    print(json.dumps(names, indent=0))
        except httpx.HTTPError as exc:      # network-class failures receipted
            rec.record(transport="mcp-http", tool="initialize",
                       request={"jsonrpc": "initialize (secrets withheld)"},
                       response={"status": None, "excerpt": repr(exc)[:200]},
                       cell="s4b-init", notes="network-class failure on /http")
            results["http_initialize"] = f"network-error"
        finally:
            pass

    # -- legacy HTTP+SSE transport -------------------------------------------
    with httpx.Client(timeout=30.0) as http:
        try:
            r = http.get(f"{BASE}/sse", headers=headers, timeout=8.0)
            rec.record(transport="mcp-http", tool="sse-handshake",
                       request={"note": "GET /sse (legacy transport attempt)"},
                       response={"status": r.status_code,
                                 "excerpt": r.text[:300],
                                 "echo_headers": {k: v for k, v in r.headers.items()
                                                  if "event" in k.lower()
                                                  or "mcp" in k.lower()}},
                       cell="s4b-sse", notes="GET /sse responded")
            results["sse"] = r.status_code
        except httpx.ReadTimeout as exc:
            # stream opened but never produced bytes within the window -
            # consistent with an OAuth-gated SSE transport; receipt the
            # silence beside the /http outcome.
            rec.record(transport="mcp-http", tool="sse-handshake",
                       request={"note": "GET /sse (legacy transport attempt)"},
                       response={"status": None,
                                 "excerpt": "stream open, NO BYTES within 8s"},
                       cell="s4b-sse",
                       notes="SSE transport silent without OAuth login; "
                             "stdio remains the verified transport")
            results["sse"] = "silent-stream"
        finally:
            pass

    print("SPIKE4B:", json.dumps(results))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
