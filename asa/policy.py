"""Policy DSL v0 engine (2026-11-08): compiled policies vs receipted behavior.

Thesis: an agent's *policy* (what it believes about money semantics) must be
checked against the receipted sandbox, not the docs. The engine evaluates a
compiled policy (policies/compiled/*.json) against two evidence stores:

  * atlas/coverage_<canon>.json  - the matrix row verdicts (PASS/DRIFT/OBSERVE)
  * runs/mcp_tools_snapshot_stdio.json - the tool surface truth

Assertion kinds supported by the v0 engine (each returns per-assertion
verdicts with counterexample citations):

  idempotent_retries   retry shapes RETRY_SAME_REQUEST_ID must collapse ids
                       for the effects listed
  tool_available       MCP tools must exist in the snapshot
  no_masked_failures   MCP tool result isError must agree with the underlying
                       application status carried in the result text
  hostile_text_rejected_script_class   script-class payloads must be rejected
                       with ONE consistent, debuggable artifact
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas"
RUNS = ROOT / "runs"

VERDICT_PASS = "PASS"
VERDICT_FAIL = "FAIL"
VERDICT_OPEN = "OPEN"      # no data in the evidence store to decide


def _rows(canon: str) -> list[dict]:
    data = json.loads((ATLAS / f"coverage_{canon}.json").read_text(encoding="utf-8"))
    return data["rows"]


def _mcp_tool_names() -> list[str]:
    snap = json.loads((RUNS / "mcp_tools_snapshot_stdio.json").read_text(encoding="utf-8"))
    return [t["name"] for t in snap["tools"]]


# ---------------------------------------------------------------------------
# assertion checkers. Each returns (verdict, note, counterexamples)
# counterexamples: list of short citation strings from the evidence store.
# ---------------------------------------------------------------------------

def _check_idempotent_retries(assertion: dict, canon: str) -> tuple:
    effects = assertion["effects"]
    ces = []
    saw_any = False
    for r in _rows(canon):
        if r.get("transport") != "rest" or not r.get("executed"):
            continue
        if r["effect"] not in effects:
            continue
        if r["shape"] != "RETRY_SAME_REQUEST_ID":
            continue
        sts = r.get("statuses") or []
        if sts and all(s >= 400 for s in sts):
            continue          # all-error pair: no object effects to idempotency-check
        saw_any = True
        cell = r["cell_id"]
        if r["verdict"] == "PASS":
            continue
        if r["verdict"] in ("DRIFT", "OBSERVE"):
            note_blob = " ".join(r.get("notes", []))
            if "ids_equal=True" in note_blob or "collapsed" in note_blob:
                continue
            ces.append(f"cell {cell:03d} {r['effect']}/{r['precondition']}: "
                       f"{r['verdict']} ({note_blob[:90]})")
    if not saw_any:
        return (VERDICT_OPEN, "no same-header retry rows executed against this canon", [])
    if ces:
        return (VERDICT_FAIL, "same-header retries did NOT collapse ids", ces)
    return (VERDICT_PASS, "same-header retries collapsed ids on all executed rows", [])


def _check_tool_available(assertion: dict, canon: str = "") -> tuple:
    have = set(_mcp_tool_names())
    missing = [t for t in assertion["tools"] if t not in have]
    if missing:
        return (VERDICT_FAIL, "tools absent from the MCP stdio surface", missing)
    return (VERDICT_PASS, "all required tools present", [])


def _check_no_masked_failures(assertion: dict, canon: str) -> tuple:
    ces = []
    saw_any = False
    for r in _rows(canon):
        if r.get("transport") != "mcp-stdio" or not r.get("executed"):
            continue
        blob = " ".join(r.get("notes", []))
        saw_any = True
        if "MASKED-FAILURE" in blob:
            ces.append(f"cell {r['cell_id']:03d}: {blob[:100]}")
    if not saw_any:
        return (VERDICT_OPEN, "no executed MCP rows in this canon", [])
    if ces:
        return (VERDICT_FAIL,
                "isError=false while result text carries ok:false (agent would act on failure)",
                ces)
    return (VERDICT_PASS, "no masked failures observed", [])


def _check_hostile_text_rejected_script_class(assertion: dict, canon: str) -> tuple:
    ces = []
    saw_any = False
    for r in _rows(canon):
        if r.get("transport") == "mcp-stdio" or not r.get("executed"):
            continue
        if r["abuse"] != "UNTRUSTED_ECHO":
            continue
        blob = " ".join(r.get("notes", []))
        if "echo=reflected-verbatim" in blob or "403" in blob or "406" in blob:
            saw_any = True
            exact = assertion.get("expected_artifact", "single debuggable 4xx json")
            if "echo=reflected-verbatim" in blob:
                ces.append(f"cell {r['cell_id']:03d}: hostile text ACCEPTED and "
                           f"stored verbatim (no rejection at all)")
            elif not any(f"[{s}]" in blob for s in (403, 406)):
                ces.append(f"cell {r['cell_id']:03d}: non-debuggable artifact {blob[:70]}")
            del exact
    if not saw_any:
        return (VERDICT_OPEN, "no executed echo rows in this canon", [])
    if ces:
        return (VERDICT_FAIL,
                "script-class payloads are not rejected by one consistent debuggable artifact",
                ces)
    return (VERDICT_PASS, "script-class payloads consistently rejected", [])


def _check_duplicate_retry_observed(assertion: dict, canon: str) -> tuple:
    """Known-hazard documentation semantics (review-vetted): the v1 policy
    ASSERTS the receipted duplicate behavior, so checker PASS = "the receipts
    still evidence the hazard" - the hazard itself is documented, not removed.
    A counterexample here means invoicing retries collapsed (behavior changed);
    the policy would then need a NEW receipted rewrite, not a silent pass.
    """
    effects = assertion["effects"]
    ces = []
    saw_any = False
    for r in _rows(canon):
        if r.get("transport") != "rest" or not r.get("executed"):
            continue
        if r["effect"] not in effects:
            continue
        if r["shape"] != "RETRY_SAME_REQUEST_ID":
            continue
        sts = r.get("statuses") or []
        if sts and all(s >= 400 for s in sts):
            continue          # all-error pair: no object effects to measure
        saw_any = True
        blob = " ".join(r.get("notes", []))
        collapsed = ("ids_equal=True" in blob or "ids collapsed" in blob
                     or "collapsed" in blob)
        if collapsed:
            ces.append(f"cell {r['cell_id']:03d}: retry COLLAPSED "
                       f"(removed the duplicate hazard): {blob[:80]}")
        # DRIFT rows ('ids DIVERGED') and OBSERVE rows ('ids_equal=False') both
        # carry the duplicate behavior this policy asserts.
    if not saw_any:
        return (VERDICT_OPEN, "no same-header retry rows executed against this canon", [])
    if ces:
        return (VERDICT_FAIL, "same-header retries collapsed (duplicate hazard gone?)", ces)
    return (VERDICT_PASS,
            "same-header retries duplicate objects on every executed row (hazard carried)", [])


_CHECKERS = {
    "idempotent_retries": _check_idempotent_retries,
    "duplicate_retry_observed": _check_duplicate_retry_observed,
    "tool_available": _check_tool_available,
    "no_masked_failures": _check_no_masked_failures,
    "hostile_text_rejected_script_class": _check_hostile_text_rejected_script_class,
}


def check_policy(policy_path: Path, canon: str) -> dict:
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    results = []
    for a in policy.get("asserts", []):
        kind = a["kind"]
        checker = _CHECKERS.get(kind)
        if checker is None:
            results.append({"kind": kind, "verdict": VERDICT_OPEN,
                            "note": f"engine v0 has no checker for {kind!r}",
                            "counterexamples": []})
            continue
        if kind == "tool_available":
            verdict, note, ces = checker(a)
        else:
            verdict, note, ces = checker(a, canon)
        results.append({"kind": kind, "verdict": verdict, "note": note,
                        "counterexamples": ces})
    failed = sum(1 for r in results if r["verdict"] == VERDICT_FAIL)
    opened = sum(1 for r in results if r["verdict"] == VERDICT_OPEN)
    overall = ("FAIL" if failed else
               "OPEN" if opened == len(results) else "PASS")
    return {"policy": policy_path.name, "overall": overall, "assertions": results}
