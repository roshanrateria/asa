"""Policy check runner (Mon 2026-11-09): compiled policies vs receipted canon.

Each compiled policy (policies/compiled/*.json) is evaluated by the v0 engine
(asa.policy) against the canonical coverage artifact. Output table + a single
JSON artifact (atlas/policy_check.json) feeding the HTML report.

Exit codes: 0 = all PASS; 2 = any FAIL (drift caught); 3 = only OPEN.
The v0 policies are EXPECTED to fail - that failure, with produced
counterexamples, is the receipt that triggers the v1 repair.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from asa.policy import ROOT, check_policy

PIONEER = sorted((ROOT / "policies" / "compiled").glob("*.json"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--canon", default="pass1d2")
    ap.add_argument("--out", default="atlas/policy_check.json")
    args = ap.parse_args()

    out = {"canon": args.canon, "checks": []}
    any_fail = any_open_only = False
    for path in PIONEER:
        res = check_policy(path, args.canon)
        out["checks"].append(res)
        print(f"{res['policy']}: {res['overall']}")
        for a in res["assertions"]:
            print(f"   {a['verdict']:<6} {a['kind']}: {a['note']}")
            for ce in a["counterexamples"][:6]:
                print(f"          - {ce}")

        if res["overall"] == "FAIL":
            any_fail = True
        elif res["overall"] == "OPEN":
            any_open_only = True

    Path("atlas").mkdir(exist_ok=True)
    Path(args.out).write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"POLICY-CHECK: {args.out} ({len(out['checks'])} policies)")
    return 2 if any_fail else (3 if any_open_only else 0)


if __name__ == "__main__":
    raise SystemExit(main())
