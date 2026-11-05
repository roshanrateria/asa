"""Cross-run forensics (2026-11-06): echo-block cells and money retry cell proof.

1. Echo text cells across three harness passes: cell 82/88 (create) and 94
   (payment note) - which status did the SAME chars payload elicit per pass?
2. pass1c retry money cells 11/26/27: proof-of-shape (same header really sent?)
"""

from __future__ import annotations

import json

RUNS = ("runs/harness-pass1.jsonl", "runs/harness-pass1b.jsonl",
        "runs/harness-pass1c.jsonl")
WANT = {"82", "88", "94"}


def main() -> None:
    print("== echo cells across passes ==")
    for path in RUNS:
        try:
            fh = open(path, encoding="utf-8")
        except FileNotFoundError:
            print(f"({path} missing)")
            continue
        for line in fh:
            r = json.loads(line)
            if r.get("cell") not in WANT:
                continue
            r = _shrink(r)
            print(f"{path[7:19]} cell {r['cell']:>2} seq {r['seq']:>3} "
                  f"[{r['response']['status']}] body={r['response']['excerpt'][:110]}")
        fh.close()

    print("\n== pass1c money retry proof-of-shape ==")
    want = ("11", "26", "27")
    for line in open("runs/harness-pass1c.jsonl", encoding="utf-8"):
        r = json.loads(line)
        if r.get("cell") not in want:
            continue
        if "RETRY" not in r.get("notes", ""):
            continue
        hoi = r["request"]["headers_of_interest"]
        print(f"cell {r['cell']:>2} seq {r['seq']:>3} "
              f"sent={str(hoi['sent_paypal_request_id'])[:12]:<12} "
              f"echoed={hoi['echoed_paypal_request_id']} "
              f"[{r['response']['status']}] ids={r['response']['ids']}")


def _shrink(r: dict) -> dict:
    out = dict(r)
    out["response"] = {"status": r["response"]["status"],
                       "excerpt": r["response"]["excerpt"] or "<EMPTY BODY>"}
    return out


if __name__ == "__main__":
    main()
