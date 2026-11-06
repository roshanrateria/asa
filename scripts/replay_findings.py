"""Replayable-finding runner (Mon 2026-11-09): headline findings, replayed live.

Each finding is re-executed in its minimal form (bounded live calls, all
receipted to runs/replay-findings.jsonl) and classified:

  REPLAYED          behavior matches the finding as receipted 2026-11-06..08
  CHANGED           sandbox produced a different observable - finding gets a
                    dated amendment (never silently rewritten)

Findings replayed:
  R1 SF-5   mis-keyed `line_items` body -> silent $0 invoice (create + read-back)
  R2 SF-1x  invoicing ignores PayPal-Request-Id (same-header pair)
  R3 SF-10  script-class payload artifact class on REST
  R4 SF-9   the same payload through MCP stdio: masked success flag

Output: console verdicts + atlas/replay_findings.json
"""

from __future__ import annotations

import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from asa import mcp_client as mcp
from asa.config import load_config
from asa.recorder import Recorder, extract_ids, excerpt_of
from asa.rest_client import RestClient

SCRIPT_PAYLOAD = "<script>alert(1)</script> ../../etc/passwd"
today = datetime.now(timezone.utc).date().isoformat()


def _artifact_class(status: int, body) -> str:
    excerpt = excerpt_of(body, limit=60) if not isinstance(body, str) else body[:60]
    if status >= 400:
        if not excerpt.strip():
            return "empty-body"
        if excerpt.lstrip().startswith("<!DOCTYPE"):
            return "waf-html-page"
        return f"json-4xx ({excerpt[:40]})"
    return "accepted-stored"


def main() -> int:
    cfg = load_config()
    rec = Recorder(cfg.runs_dir, "replay-findings")
    rc = RestClient(cfg, rec)
    results = []

    def emit(fid: str, finding: str, verdict: str, detail: str) -> None:
        results.append({"finding": fid, "label": finding, "verdict": verdict,
                        "detail": detail, "replayed_on": today})
        print(f"[{fid}] {verdict} | {finding} | {detail[:120]}")

    try:
        # ---- R1 (SF-5): silent $0 invoice via mis-keyed body ----------------
        status, body, _ = rc.call(
            "POST", "/v2/invoicing/invoices",
            json={"detail": {"currency_code": "USD"},
                  "line_items": [{"name": "asa replay probe",
                                  "unit_amount": {"currency_code": "USD",
                                                  "value": "20.00"},
                                  "quantity": "1"}]},
            cell="replay-r1", notes="replay R1 mis-keyed line_items create")
        inv_id = (body.get("id") if isinstance(body, dict) else None) or \
            (extract_ids(body)[0] if isinstance(body, dict) and extract_ids(body) else None)
        zero, paths = None, []
        if inv_id and status < 300:
            gstatus, gbody, _ = rc.get_invoice(inv_id, cell="replay-r1",
                                               notes="replay R1 read-back")

            def amount_paths(obj, base="$"):
                """every dict under an amount-ish key that carries a value"""
                out = []
                if isinstance(obj, dict):
                    for k, v in obj.items():
                        p = f"{base}.{k}"
                        if "amount" in k.lower() and isinstance(v, dict) \
                                and v.get("value") is not None:
                            out.append((p, v.get("value")))
                        out.extend(amount_paths(v, p))
                elif isinstance(obj, list):
                    for i, v in enumerate(obj):
                        out.extend(amount_paths(v, f"{base}[{i}]"))
                return out

            paths = amount_paths(gbody) if isinstance(gbody, dict) else []
            zero = [p for p, v in paths if str(v) == "0.00"]
        if zero:
            emit("R1 (SF-5)", "mis-keyed money field silently zeroed",
                 "REPLAYED",
                 f"created {inv_id}, amount paths at 0.00: {zero[:3]} "
                 f"(all amount paths: {paths[:5]})")
        else:
            emit("R1 (SF-5)", "mis-keyed money field silently zeroed",
                 "CHANGED",
                 f"status {status}; amounts found: {paths[:5]}; full wire in runs/")

        # ---- R2 (SF-1x): invoicing ignores PayPal-Request-Id ---------------
        fixed = str(uuid.uuid4())
        pair_ids = []
        for i in range(2):
            s, b, _ = rc.call("POST", "/v2/invoicing/invoices",
                              json={"detail": {"currency_code": "USD"},
                                    "items": [{"name": "asa replay probe",
                                               "unit_amount": {"currency_code": "USD",
                                                               "value": "5.00"},
                                               "quantity": "1"}]},
                              headers={"PayPal-Request-Id": fixed},
                              cell="replay-r2",
                              notes=f"replay R2 same-header create #{i}")
            pair_ids.extend(extract_ids(b) if isinstance(b, dict) else [])
        distinct = len(set(pair_ids))
        if distinct == 2:
            emit("R2 (SF-1x)", "invoicing ignores PayPal-Request-Id",
                 "REPLAYED", f"same header -> {distinct} distinct invoices")
        else:
            emit("R2 (SF-1x)", "invoicing ignores PayPal-Request-Id",
                 "CHANGED", f"same header -> {distinct} distinct ({pair_ids})")

        # ---- R3 (SF-10): script payload artifact class on REST -------------
        s3, b3, _ = rc.call("POST", "/v2/invoicing/invoices",
                            json={"detail": {"currency_code": "USD",
                                             "note": SCRIPT_PAYLOAD},
                                  "items": [{"name": "asa replay probe",
                                             "unit_amount": {"currency_code": "USD",
                                                             "value": "5.00"},
                                             "quantity": "1"}]},
                            cell="replay-r3",
                            notes="replay R3 script payload in note")
        emit("R3 (SF-10)", "script payload artifact split (406-empty / 403-waf / stored)",
             "REPLAYED" if s3 >= 400 else "CHANGED",
             f"status {s3} artifact={_artifact_class(s3, b3)}")

        # ---- R4 (SF-9): MCP masks the same rejection -------------------------
        os.environ["PAYPAL_ACCESS_TOKEN"] = rc._token_fetch()
        import asyncio

        async def r4() -> tuple[bool, str]:
            session = mcp.McpStdioSession(cfg)
            try:
                await session.open()
                result = await session.call_tool(
                    "create_invoice", {
                        "currency_code": "USD",
                        "primary_recipients": [{"billing_info": {
                            "email_address": "invoice-anchor@example.com"}}],
                        "items": [{"name": "asa replay probe",
                                   "unit_amount": {"currency_code": "USD",
                                                    "value": "5.00"},
                                   "quantity": "1"}],
                        "note": SCRIPT_PAYLOAD,
                    })
                joined = " ".join(result.get("texts", []))
                return bool(result.get("ok")), joined
            finally:
                await session.close()

        ok_flag, joined = asyncio.run(r4())
        rec.record(transport="mcp-stdio", tool="create_invoice",
                   request={"note": SCRIPT_PAYLOAD[:40]},
                   response={"status": 200 if ok_flag else 499,
                             "excerpt": joined[:400]},
                   cell="replay-r4", notes="replay R4 mcp masked failure?")
        masked = ok_flag and '"ok":false' in joined
        emit("R4 (SF-9)", "MCP tool result masks app failure as success",
             "REPLAYED" if masked else "CHANGED",
             f"ok_flag={ok_flag}, text_carries_ok_false={'\"ok\":false' in joined}")
    finally:
        rc.close()

    out_path = Path("atlas") / "replay_findings.json"
    Path("atlas").mkdir(exist_ok=True)
    out_path.write_text(json.dumps({"replayed_on": today, "results": results},
                                   indent=1), encoding="utf-8")
    repled = sum(1 for r in results if r["verdict"] == "REPLAYED")
    print(f"REPLAY: {repled}/{len(results)} findings replayed; {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
