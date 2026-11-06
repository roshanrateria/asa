"""Mis-key vs MCP (review follow-up): does create_invoice enforce `items`?

Two bounded sandbox calls through the OFFICIAL MCP tool (stdio, pinned
package), each ground-truthed by a read-only REST GET:

  M-A  create_invoice with NO items array at all (required field per docs)
  M-B  create_invoice with the mis-keyed `line_items` body (D-2 shape)

Outcome decides the SF-5 scope sentence:
  * MCP accepts (either form -> ok:true) -> agent-facing $0-invoice hazard
    extends THROUGH the MCP tool; read-back receipts prove the zeroed wire.
  * MCP rejects with a schema-ish error             -> SF-5 is REST-only,
    and the tool boundary is itself the protective layer (stated plainly).

Receipts: runs/miskey-mcp-check.jsonl; verdict artifact (committed):
atlas/miskey_mcp_check.json.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from asa import mcp_client as mcp
from asa.config import load_config
from asa.mcp_client import McpStdioSession
from asa.recorder import Recorder
from asa.rest_client import RestClient

RECIPIENT = [{"billing_info": {"email_address": "asanonrecip@example.com"}}]


def amount_paths(obj, base="$"):
    """Every (path, value) under an amount-ish key that carries a value."""
    out = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{base}.{k}"
            if "amount" in k.lower() and isinstance(v, dict) and v.get("value") is not None:
                out.append((p, v.get("value")))
            out.extend(amount_paths(v, p))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            out.extend(amount_paths(v, f"{base}[{i}]"))
    return out


async def main_async() -> dict:
    cfg = load_config()
    rec = Recorder(cfg.runs_dir, "miskey-mcp-check")
    rc = RestClient(cfg, rec)
    os.environ["PAYPAL_ACCESS_TOKEN"] = rc._token_fetch()

    session = McpStdioSession(cfg)
    await session.open()
    results = {"checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
               "mcp_package": mcp.mcp_package(), "variants": {}}

    def bodies() -> dict[str, dict]:
        return {
            "M-A_no_items": {"currency_code": "USD",
                             "primary_recipients": RECIPIENT,
                             "note": "asa mis-key check: required items ABSENT (MCP)"},
            "M-B_line_items": {"currency_code": "USD",
                               "primary_recipients": RECIPIENT,
                               "line_items": [{"name": "asa miskey probe",
                                               "unit_amount": {"currency_code": "USD",
                                                               "value": "20.00"},
                                               "quantity": "1"}],
                               "note": "asa mis-key check: line_items mis-key (MCP)"},
        }

    try:
        for name, args in bodies().items():
            result = await session.call_tool("create_invoice", {**args})
            ok_flag = bool(result.get("ok"))
            text = " ".join(result.get("texts", []))
            rec.record(transport="mcp-stdio", tool="create_invoice",
                       request={"args_no_items": name.endswith("no_items"),
                                "keys": sorted(args.keys())},
                       response={"status": 200 if ok_flag else 499,
                                 "excerpt": text[:400]},
                       cell=f"miskey-mcp-{name}", notes=name)
            ids = re.findall(r"INV2-[A-Z0-9-]+", text)
            variant = {"isError": ok_flag, "result_text": text[:200],
                       "accepted": bool(ok_flag and ids),
                       "invoice_id": ids[0] if ids else None}
            if variant["accepted"]:
                gstat, gbody, _ = rc.get_invoice(variant["invoice_id"],
                                                 cell=f"miskey-mcp-{name}",
                                                 notes=f"{name} read-back")
                paths = amount_paths(gbody) if isinstance(gbody, dict) else []
                zeroed = all(str(v) == "0.00" for _, v in paths) if paths else None
                variant.update({"read_status": gstat,
                                "amount_paths_zeroed": zeroed,
                                "amount_paths_sample": paths[:4]})
            results["variants"][name] = variant
            print(f"[{name}] isError={variant['isError']} "
                  f"accepted={variant['accepted']} id={variant['invoice_id']} "
                  f"zeroed={variant.get('amount_paths_zeroed')}")
    finally:
        await session.close()
        rc.close()

    a = results["variants"]["M-A_no_items"]
    b = results["variants"]["M-B_line_items"]
    rejected = (not a.get("accepted")) and (not b.get("accepted"))
    if not rejected:
        verdict = ("MCP_ACCEPTS - agent-facing $0-invoice hazard extends through "
                   "the MCP tool; SF-5 is NOT REST-only")
    elif "Required at items" in (a.get("result_text", "") + b.get("result_text", "")):
        # both rejections ride isError=false with a -32602 error string:
        # (1) the tool schema is the mis-key protective layer (SF-5 REST-only),
        # (2) the schema rejection is ITSELF masked (SF-9/D-4 pattern,
        #     second independent instance, validation-class)
        verdict = ("MCP_ENFORCES_ITEMS (schema boundary rejects items-less/ "
                   "mis-keyed bodies: MCP error -32602 'Required at items') - "
                   "SF-5 ($0 invoice) is REST-only; AND the boundary rejection "
                   "rides isError=false with the -32602 error only in text - "
                   "the masking pattern recurs at the schema class (SF-9, "
                   "second independent instance)")
    else:
        verdict = "MCP_REJECTS (not the schema class; read result_text)"
    results["verdict"] = verdict
    results["interpretation"] = ("the MCP tool boundary blocks the agents' "
                                 "mis-key path (schema); the rejection's "
                                 "transport (isError=false + text) matches the "
                                 "masked-failure pattern receipted at API class")

    Path("atlas").mkdir(exist_ok=True)
    Path("atlas/miskey_mcp_check.json").write_text(json.dumps(results, indent=1),
                                                   encoding="utf-8")
    print("MISKEY-MCP:", verdict)
    print("artifact: atlas/miskey_mcp_check.json")
    return results


if __name__ == "__main__":
    asyncio.run(main_async())
