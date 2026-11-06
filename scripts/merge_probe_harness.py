"""Merge the opencode-subagent harness legs into atlas/agent_probe.json.

agent_probe.py subprocess runs carry the NVIDIA legs only (the long-running
HTTP measurement); the cross-engine subagent trials are collected by hand into
atlas/_probe_harness_answers.json. This script appends those legs to the
committed artifact WITHOUT re-running the NVIDIA measurement, recomputes the
per-row Wilson summary, and reports the combined counts on stdout.

Run AFTER agent_probe.py finishes an NVIDIA sweep:
    python scripts\\merge_probe_harness.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.agent_probe import HAZARD_VERDICTS, hazard_counts, wilson  # noqa: E402

PROBE_PATH = ROOT / "atlas" / "agent_probe.json"
SIDECAR_PATH = ROOT / "atlas" / "_probe_harness_answers.json"


def main() -> int:
    payload = json.loads(PROBE_PATH.read_text(encoding="utf-8"))
    sidecar = json.loads(SIDECAR_PATH.read_text(encoding="utf-8"))

    existing = {(p["leg"], p.get("engine") or p.get("model"), p["probe"])
                for p in payload["probes"]}
    added = 0
    for row in sidecar.get("harness_legs", []):
        key = (row["leg"], row.get("engine") or row.get("model"), row["probe"])
        if key in existing:
            # upsert: refresh counts/samples/n from the sidecar (single source)
            for i, p in enumerate(payload["probes"]):
                if (p["leg"], p.get("engine") or p.get("model"), p["probe"]) == key:
                    payload["probes"][i] = row
        else:
            payload["probes"].append(row)
            added += 1

    summary_rows = []
    for row in payload["probes"]:
        if row.get("error"):
            continue                     # unavailable legs stay visible, unchecked
        probe = row["probe"]
        n = sum(row["counts"].values())
        k = hazard_counts(probe, row["counts"])
        lo, hi = wilson(k, n)
        summary_rows.append({
            "leg": row["leg"], "model": row.get("engine") or row["model"],
            "probe": probe,
            "n": n, "counts": row["counts"],
            "hazard_classes": list(HAZARD_VERDICTS.get(probe, ())),
            "hazard_count": k,
            "hazard_share_wilson95": f"{k}/{n} ({(k / n if n else 0):.2f}) "
                                     f"[{lo:.2f}, {hi:.2f}]" if n else "n/a",
        })
    payload["summary_rows"] = summary_rows
    payload["harness_merge"] = {
        "merged_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "sidecar": "atlas/_probe_harness_answers.json",
        "rows_added": added,
        "qwen_note": sidecar.get("note", ""),
    }
    PROBE_PATH.write_text(json.dumps(payload, indent=1), encoding="utf-8")
    print(f"MERGED +{added} harness legs -> {PROBE_PATH.relative_to(ROOT)}")
    for s in summary_rows:
        print(f"  {s['leg']}/{s['model']}/{s['probe']}: {s['hazard_share_wilson95']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
