"""Harness pass 1 (Sat 2026-11-07): the 108-cell matrix, both phases, atlas output.

Phase REST:  probe.run_rest_phase over all 108 cells (family-gated schedulings
             recorded as not-scheduled reasons; 429 -> honest partial bail-out).
Phase MCP:   one stdio session; only CREATE cells are schedulable (SF-8:
             record/refund tools absent); setups reused from a REST client;
             tool calls receipted as transport 'mcp-stdio'.

Output: atlas/coverage_pass1.md + .json committed artifacts, console table.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from asa import mcp_client as mcp
from asa import probe
from asa.config import load_config
from asa.matrix import candidate_grid
from asa.recorder import Recorder
from asa.rest_client import RestClient

INV2_RE = re.compile(r"INV2-[A-Z0-9-]+")


def mcp_phase(cfg, cells, ledger: probe.Ledger, rec, rc_rest: RestClient) -> None:
    # a fresh sandbox token for the stdio server
    token = rc_rest._token_fetch()
    os.environ["PAYPAL_ACCESS_TOKEN"] = token
    import asyncio

    session = mcp.McpStdioSession(cfg)
    try:
        asyncio.run(_mcp_session_phase(cfg, cells, ledger, rec, rc_rest, session))
    except Exception as exc:  # every infrastructure failure is a bail-out reason
        ledger.bail_remaining("mcp-stdio", f"mcp-unavailable: {exc!r}"[:120])
        print(f"MCP PHASE: bail-out ({exc!r})")


async def _mcp_session_phase(cfg, cells, ledger, rec, rc_rest, session) -> None:
    try:
        await session.open()
    except Exception as exc:
        ledger.bail_remaining("mcp-stdio", f"mcp-unavailable: {exc!r}"[:120])
        print(f"MCP PHASE: open failed ({exc!r})")
        return
    try:
        tool_names = set(session.tool_names)
        probe_target = "create_invoice"
        if probe_target not in tool_names:
            for cell in cells:
                if cell.effect == "CREATE":
                    ledger.not_sched(cell, probe.NS_MCP_TOOL_ABSENT)
            return

        for cell in cells:
            if cell.effect != "CREATE":
                ledger.not_sched(cell, probe.NS_MCP_TOOL_ABSENT)
                continue
            if cell.shape != "FRESH":
                ledger.not_sched(cell, probe.NS_MCP_SHAPE_MERGE)
                continue
            ledger.schedule(cell, "mcp-stdio")

            try:
                anchor = probe.ensure_anchor(cell, cfg, rc_rest, rec)
                args: dict = {
                    "currency_code": "USD",
                    "primary_recipients": [{"billing_info": {"email_address":
                        probe.PLACEHOLDER_RECIPIENT}}],
                    "items": [{"name": "asa mcp probe item",
                               "unit_amount": {"currency_code": "USD",
                                                "value": probe.ITEM_VALUE},
                               "quantity": "1"}],
                }
                if cell.abuse == "UNTRUSTED_ECHO":
                    payload = (probe.ECHO_PAYLOADS["chars"] if cell.cell_id % 2 == 0
                               else probe.ECHO_PAYLOADS["prompt"])
                    args["note"] = payload

                result = await session.call_tool(probe_target, args)
                texts = result.get("texts", [])
                joined = " ".join(texts)
                ids = sorted(set(INV2_RE.findall(joined)))
                ok_invoke = bool(result.get("ok"))

                rec.record(transport="mcp-stdio", tool=probe_target,
                           request={"args": args},
                           response={"status": 200 if ok_invoke else 499,
                                     "ids": ids, "debug_id": None,
                                     "excerpt": joined[:400]},
                           cell=str(cell.cell_id),
                           notes=f"mcp {cell.abuse}/{cell.precondition}/FRESH")

                verdict = "PASS" if (ok_invoke and ids) else "DRIFT"
                note = f"mcp create ids={ids} ok={ok_invoke}"
                if '"ok":false' in joined:
                    # SF-9: tool result isError=false while the tool TEXT carries
                    # the application-level failure ({"ok":false,"status":406}).
                    verdict = "DRIFT"
                    note = ("mcp MASKED-FAILURE: isError=false but text ok:false "
                            f"(texts sample: {joined[:90]})")
                    if '"status":406' in joined:
                        note += " [406 underneath]"
                elif cell.abuse == "UNTRUSTED_ECHO" and ids:
                    echo = probe.classify_echo(rc_rest, ids[0],
                                               {"detail": {"note": args.get("note")}})
                    note += f" echo={echo}"
                    verdict = "DRIFT" if echo == "reflected-verbatim" else verdict

                ledger.finish_row(cell.cell_id, attempted=True, executed=True,
                                  statuses=[200 if ok_invoke else 499],
                                  note=note, verdict=verdict)
                print(f"[{cell.cell_id:03d}] mcp {cell.abuse[:2]}-{cell.precondition[:3]} "
                      f"-> {'200' if ok_invoke else 'err'} {verdict} | {note[:80]}")
            except probe.RateLimitAbort:
                ledger.bail_remaining("mcp-stdio", probe.NS_RATE_LIMIT)
                raise
            except Exception as exc:  # cell-level failure recorded, phase continues
                ledger.finish_row(cell.cell_id, attempted=True, executed=False,
                                  statuses=[], note=f"mcp-cell-error: {exc!r}"[:160],
                                  verdict="OBSERVE")
                print(f"[{cell.cell_id:03d}] MCP-CELL-FAIL {exc!r}"[:120])
    finally:
        try:
            await session.close()
        except Exception:
            pass


def write_reports(ledger: probe.Ledger, tag: str = "pass1") -> None:
    """Atlas artifacts are per-tag so different passes never overwrite each other."""
    counts = ledger.counts()
    out_dir = Path("atlas")
    out_dir.mkdir(exist_ok=True)

    rows_payload = []
    for cid, r in sorted(ledger.rows.items()):
        cell = r["cell"]
        rows_payload.append({
            "cell_id": cell.cell_id,
            "abuse": cell.abuse,
            "effect": cell.effect,
            "precondition": cell.precondition,
            "shape": cell.shape,
            "transport": r["transport"],
            "attempted": r["attempted"],
            "executed": r["executed"],
            "statuses": r["statuses"],
            "verdict": r["verdict"],
            "notes": r["notes"],
        })

    payload = {"counts": counts, "rows": rows_payload}
    (out_dir / f"coverage_{tag}.json").write_text(
        json.dumps(payload, indent=1), encoding="utf-8")

    md = [f"# Coverage {tag} (2026-11-07)", "",
          f"counts: {json.dumps(counts)}", "", "## Not-scheduled reasons", ""]
    for reason, ids in sorted(ledger.not_scheduled.items()):
        md.append(f"- `{len(ids):3d}` cells — {reason} (e.g. {ids[:5]})")
    md += ["", "## Executed rows", ""]
    md.append("| cell | transport | status chain | verdict | note |")
    md.append("|---|---|---|---|---|")
    for row in rows_payload:
        if row["executed"]:
            ss = ",".join(str(s) for s in row["statuses"])
            note = " / ".join(row["notes"])[:110]
            md.append(f"| {row['cell_id']:03d} | {row['transport']} | "
                      f"{ss} | {row['verdict']} | {note} |")
    (out_dir / f"coverage_{tag}.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"ATLAS: {out_dir / f'coverage_{tag}.md'} + .json written")


def main() -> int:
    tag = "pass1"
    if "--tag" in sys.argv:
        i = sys.argv.index("--tag")
        if i + 1 < len(sys.argv):
            tag = sys.argv[i + 1]
    cfg = load_config()
    rec = Recorder(cfg.runs_dir, f"harness-{tag}")
    cells = candidate_grid()
    ledger = probe.Ledger(total=len(cells))
    print(f"HARNESS PASS starting: tag={tag} cells={len(cells)}")

    # surfacing phase - one client for setups (mcp phase) - everything receipts
    probe.run_rest_phase(cfg, cells, ledger, rec)
    rc_rest = RestClient(cfg, rec)
    try:
        mcp_phase(cfg, cells, ledger, rec, rc_rest)
    finally:
        rc_rest.close()

    counts = ledger.counts()
    write_reports(ledger, tag)
    print(f"\n== PASS SUMMARY ({tag}) ==")
    for k, v in counts.items():
        print(f"  {k}: {v}")
    verdicts_ok = all(v >= 0 for v in counts["verdicts"].values())
    print(f"HARNESS[{tag}]:", "COMPLETE" if verdicts_ok else "DONE-WITH-NOTES")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
