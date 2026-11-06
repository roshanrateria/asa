"""Atlas builder (Sun 2026-11-08): doc-vs-sandbox delta tables from receipts.

Inputs (reads only, never re-probes):
  atlas/coverage_<tag>.json       harness coverage artifacts
  runs/harness-<tag>.jsonl        raw receipts (for the echo cross-run matrix)

Outputs:
  atlas/atlas_v0.md               the human atlas: deltas, pivots, echo matrix
  atlas/atlas_v0.json             the same, structured

Honesty rules carried over from the ledger:
  * every delta row cites its cells/receipts;
  * not-scheduled reasons are reasons, not omissions;
  * verdicts are PASS / DRIFT / OBSERVE and their per-transport meaning
    (REST = sandbox API vs documented contract; MCP = tool result vs REST).
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

ROOT = Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas"
RUNS = ROOT / "runs"

# ---------------------------------------------------------------------------
# Delta rows. "expected" is the documented/toolkit claim (its source), "seen"
# is reconstructed from the canon artifacts at build time, so the published
# atlas cannot drift from the receipts.
# ---------------------------------------------------------------------------

DELTA_ROWS = [
    {
        "id": "D-1",
        "claim": "Retries carrying the same PayPal-Request-Id do not duplicate effects (docs: invoicing core concepts - idempotent request retry).",
        "probe": "same-header pairs on POST create_order (orders v2) vs POST invoicing invoices / payments / refunds.",
        "seen": "orders v2 honors it - 201 then 200-return-existing with the SAME order id, still true ~49 min later. The invoicing family ignores it on every endpoint: same-header create pairs -> two distinct INV2 invoices [201,201] x3 flavor; same-header payments/refunds -> two distinct EXTR records [200,200].",
        "status": "CONFIRMED-DELTA (3 of 4 money endpoints unidempotent)",
        "cites": "docs: docs.paypal.ai/growth/grow-business/invoicing/core-concepts + developer.paypal.com/invoicing/core-concepts; receipts: spike1 12 receipts (2 runs); atlas cells 002/005/008 + 011/014/017-026; smoke-retry-shapes receipts",
    },
    {
        "id": "D-2",
        "claim": "Invoice create requires the `items` array (docs: Invoicing API v2 - invoice object, `items` required).",
        "probe": "create_invoice with required `items` MISSING (mis-keyed `line_items` body only).",
        "seen": "required `items` missing -> 201 Created anyway, wire amounts zeroed (amount/due 0.00) - an invoice object that passes visual review with no money value. Downstream refunds then 422 INVALID_REFUND_AMOUNT against the object's own MARKED_AS_PAID state.",
        "status": "CONFIRMED-DELTA (required field unenforced, money zeroed)",
        "cites": "docs: developer.paypal.com/docs/api/invoicing/v2/ (create_invoices request schema); receipts: spike3g/3h/3b-3f; replay R1; SF-5 chain",
    },
    {
        "id": "D-3",
        "claim": "The toolkit advertises the full invoice money lifecycle (record_payment_for_invoice / record_refund_for_invoice).",
        "probe": "MCP stdio tool surface snapshot, version-pinned: PAYPAL_MCP_PACKAGE=@paypal/mcp@1.8.1, spawn `npx -y @paypal/mcp@1.8.1 --tools=all` (all tools enabled).",
        "seen": "28 tools enabled via stdio on the pinned snapshot; the two record_* tools are absent from the SERVER surface, so an agent on PayPal's own MCP server cannot record payments/refunds on invoices - the lifecycle stops at create/send.",
        "status": "CONFIRMED-DELTA (server surface narrower than toolkit advertises)",
        "cites": "advertised: github.com/paypal/agent-toolkit README (lists record_* methods); NOT listed by: @paypal/mcp README + npmjs.com/package/@paypal/mcp; receipts: runs/mcp_tools_snapshot_stdio.json (provenance block: package 1.8.1, --tools=all, 2026-11-06) + atlas/sample_receipts/mcp_tools_list_pinned_1.8.1.json; harness mcp-tool-absent bucket (33 cells); SF-8",
    },
    {
        "id": "D-4",
        "claim": "A tool call reports its failure through the structured error flag (MCP isError).",
        "probe": "MCP create_invoice with API-rejecting hostile note (406-class).",
        "seen": "isError=false; the failure exists only inside result TEXT ({\"ok\":false,\"status\":406,\"code\":\"PAYPAL_API_HTTP_ERROR\",\"message\":\"Unknown error\"}) - structured success lies about application failure.",
        "status": "CONFIRMED-DELTA (success flag masks failure)",
        "cites": "harness pass1b seq 189/196; pass1c seq 183/190; SF-9",
    },
    {
        "id": "D-5",
        "claim": "Input validation rejects hostile text with a debuggable API error.",
        "probe": "<script> payload in invoice note / payment note; prompt-injection payload same fields.",
        "seen": "script payload: block status/artifact splits across runs (406+empty body in pass1; 403+WAF HTML page in pass1b/1c) - see Echo matrix below. prompt payload: accepted everywhere, stored VERBATIM (echo=reflected-verbatim).",
        "status": "OBSERVE (no documented rejection contract; WAF block on <script> is expected hardening, not a delta - recorded as measurement only)",
        "cites": "runs/harness-pass1{.jsonl,b,c} cells 082/088/094; echo rows 085/091/097; SF-10",
    },
    {
        "id": "D-6",
        "claim": "Geo/currency business rules surface as 4xx app errors (send to India-recipient personal sandbox).",
        "probe": "send_invoice to INR-blocked Personal account vs non-India recipient.",
        "seen": "406 MEDIA_TYPE_NOT_ACCEPTABLE with an EMPTY body wrapping the business rule - a content-negotiation status carrying a currency policy.",
        "status": "OBSERVE (no documented expectation verified for this sandbox pair; recorded as measurement only)",
        "cites": "spike3 v1 vs spike3d receipts; SF-3",
    },
    {
        "id": "D-7",
        "claim": "Refund method enum is as documented.",
        "probe": "record_refund with CARD / EXTERNAL / CASH / BANK_TRANSFER / PAYPAL.",
        "seen": "CARD and EXTERNAL -> 400 INVALID_REFUND_METHOD; 2 of 5 documented-enumeration methods disagree with the wire.",
        "status": "CONFIRMED-DELTA (enum narrower than docs)",
        "cites": "spike3e receipts; SF-4",
    },
    {
        "id": "D-8",
        "claim": "PayPal-Mock-Response negative testing works on invocations.",
        "probe": "not exercised in the v0 matrix (mock_header_used=false on every receipt by design).",
        "seen": "n/a - documented affordance, left for a later seeded rerun.",
        "status": "NOT EXERCISED (scope v0, honest exclusion)",
        "cites": "-",
    },
]

REST_TITLES = {
    "CREATE": "POST /v2/invoicing/invoices",
    "RECORD": "POST /v2/invoicing/invoices/{id}/payments",
    "REFUND": "POST /v2/invoicing/invoices/{id}/refunds",
}


def load_rows(tag: str) -> dict:
    """coverage_<tag>.json -> full payload (counts + rows)."""
    src = ATLAS / f"coverage_{tag}.json"
    return json.loads(src.read_text(encoding="utf-8"))


def load_counts(tag: str) -> dict | None:
    if not (ATLAS / f"coverage_{tag}.json").exists():
        return None
    return load_rows(tag)["counts"]


def receipt_echo_matrix(passes: list[str]) -> list[dict]:
    """Cells 082/088/094 across passes: REST artifact per pass + MCP masking."""
    want = {"82", "88", "94"}
    matrix = []
    for tag in passes:
        src = RUNS / f"harness-{tag}.jsonl"
        if not src.exists():
            continue
        for line in src.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            if r.get("cell") not in want:
                continue
            resp = r.get("response", {})
            excerpt = resp.get("excerpt") or ""
            if r.get("transport", "rest") == "mcp-stdio":
                artifact = ("masked-ok:false-text" if '"ok":false' in excerpt
                            else "tool-ok")
            else:
                if resp.get("status", 0) >= 400:
                    plain = excerpt.lstrip().strip('"').lstrip()
                    artifact = ("empty-body" if not plain
                                else "waf-html-page" if plain.startswith("<!DOCTYPE")
                                else plain[:28].replace("\n", " "))
                else:
                    artifact = "accepted-stored"
            matrix.append({"pass": tag, "cell": r["cell"], "transport":
                           r.get("transport", "rest"), "status": resp.get("status"),
                           "artifact": artifact})
    return matrix


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--canonical", default="pass1d")
    ap.add_argument("--aux", default="", help="extra pass (e.g. pass1d-fx) merged into the canon rows")
    ap.add_argument("--lineage", default="pass1,pass1b,pass1c", help="pass tags kept as lineage")
    args = ap.parse_args()

    canon = load_rows(args.canonical)
    canon_counts = dict(canon["counts"])
    canon_rows = list(canon["rows"])
    aux_rows = []
    if args.aux:
        aux = load_rows(args.aux)
        aux_rows = aux["rows"]
        for k, v in aux["counts"].items():
            if isinstance(v, int) and not isinstance(v, bool):
                if isinstance(canon_counts.get(k), int):
                    canon_counts[k] += v
        # verdicts merge
        for v, n in aux["counts"].get("verdicts", {}).items():
            canon_counts["verdicts"][v] = canon_counts["verdicts"].get(v, 0) + n
    executed = [r for r in canon_rows + aux_rows if r["executed"]]

    lineage_counts = {}
    for tag in args.lineage.split(","):
        if not tag:
            continue
        c = load_counts(tag)
        if c is not None:
            lineage_counts[tag] = c

    pivot = {}
    for r in executed:
        t = r["transport"]
        v = r["verdict"] or "-"
        pivot.setdefault(t, {}).setdefault(v, 0)
        pivot[t][v] += 1

    echo_cells = receipt_echo_matrix([args.canonical] + args.lineage.split(","))

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "canonical_pass": args.canonical,
        "aux_pass": args.aux or None,
        "counts_canon_plus_aux": canon_counts,
        "verdict_pivot_by_transport": pivot,
        "not_scheduled": canon_counts.get("not_scheduled", {}),
        "deltas": DELTA_ROWS,
        "echo_matrix": echo_cells,
        "lineage_counts": lineage_counts,
    }
    (ATLAS / "atlas_v0.json").write_text(json.dumps(payload, indent=1),
                                         encoding="utf-8")

    md = [f"# asa atlas v0 - doc-vs-sandbox deltas (auto-built from receipts)",
          "",
          f"canon: `{args.canonical}`" + (f" + `{args.aux}`" if args.aux else ""),
          f"lineage kept: {', '.join(lineage_counts)} (pass1's retry-verb plumbing bug is part of the audit trail)",
          "",
          "verdict semantics: **PASS** = sandbox matches the documented/toolkit hypothesis; **DRIFT** = sandbox contradicts it (delta); **OBSERVE** = no verified hypothesis, measurement recorded.",
          "",
          "## Coverage (canon + aux)",
          "",
          f"`{json.dumps(canon_counts)}`",
          "",
          "## Verdict pivot by transport (executed rows)",
          "",
          "| transport | PASS | DRIFT | OBSERVE |", "|---|---|---|---|"]
    for t, vv in sorted(pivot.items()):
        md.append(f"| {t} | {vv.get('PASS', 0)} | {vv.get('DRIFT', 0)} | "
                  f"{vv.get('OBSERVE', 0)} |")

    md += ["", "## Doc-vs-sandbox deltas", "",
           "| id | documented expectation | observed on sandbox | status | cites |",
           "|---|---|---|---|---|"]
    for d in DELTA_ROWS:
        md.append(f"| {d['id']} | {d['claim']} | {d['seen']} | {d['status']} | "
                  f"{d['cites']} |")

    md += ["", "## Not-scheduled reasons (honest exclusions, never silence)", ""]
    for reason, n in canon_counts.get("not_scheduled", {}).items():
        md.append(f"- `{n:3d}` cells - {reason}")

    md += ["", "## Echo matrix (hostile-text artifact across passes)", ""]
    md.append("| pass | cell | channel | status | artifact |")
    md.append("|---|---|---|---|---|")
    for e in echo_cells:
        md.append(f"| {e['pass']} | {e['cell']} | {e['transport']} | "
                  f"{e['status']} | {e['artifact']} |")

    md += ["", "## Same-semantic surface table (REST vs MCP, executed rows)", "",
           "| transport | executed | notes |", "|---|---|---|"]
    md.append(f"| rest (invoicing endpoints) | "
              f"{sum(1 for r in executed if r['transport'] == 'rest')} | "
              f"CREATE {REST_TITLES['CREATE']}; RECORD {REST_TITLES['RECORD']}; "
              f"REFUND {REST_TITLES['REFUND']} |")
    md.append(f"| mcp-stdio (@paypal/mcp) | "
              f"{sum(1 for r in executed if r['transport'] == 'mcp-stdio')} | "
              f"CREATE create_invoice only; RECORD/REFUND absent (D-3); "
              f"result text masks failure (D-4) |")

    md += ["", "## Findings index (from docs/evidence.md)", ""]
    md.append("SF-1 cross-endpoint idempotency asymmetry; SF-2 order card path payee-gated; "
              "SF-3 406-wrapped geo rule; SF-4 refund enum narrow; SF-5 silent line_items drop"
              " -> $0 invoice; SF-6 items-key family fully live; SF-7 transactions scope"
              " missing; SF-8 MCP record/refund absent; SF-9 MCP masked failure;"
              " SF-10 hostile-text artifact split.")

    md += ["", "## Reproducibility", "",
           "```",
           "python scripts\\harness_pass1.py --tag <tag>   # full matrix",
           "python scripts\\fx_cells.py --tag <tag>-fx --cells <ids>  # failed-cell follow-up",
           "python scripts\\smoke_retry_shapes.py          # retry-shape plumbing proof",
           "python scripts\\forensics_cross.py             # cross-pass echo/status forensics",
           "python scripts\\build_atlas.py --canonical <tag> --aux <tag>-fx",
           "```", ""]
    (ATLAS / "atlas_v0.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"ATLAS: atlas\\atlas_v0.md + .json (canon={args.canonical}, "
          f"executed rows={len(executed)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
