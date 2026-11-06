"""Generic follow-up runner (2026-11-06): re-execute specific cells after
transient setup failures, tagged so receipts/atlas stay separate.

Usage:
  python scripts\fx_cells.py --tag pass1d-fx --cells 16,17
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from asa import probe
from asa.config import load_config
from asa.matrix import candidate_grid
from asa.recorder import Recorder
from scripts.harness_pass1 import write_reports


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    ap.add_argument("--cells", required=True, help="comma-separated cell ids")
    args = ap.parse_args()

    want = {int(x) for x in args.cells.split(",")}
    cfg = load_config()
    rec = Recorder(cfg.runs_dir, f"harness-{args.tag}")
    cells = [c for c in candidate_grid() if c.cell_id in want]
    ledger = probe.Ledger(total=len(cells))
    print(f"fx [{args.tag}]: re-running cells {sorted(want)}")
    probe.run_rest_phase(cfg, cells, ledger, rec)
    write_reports(ledger, args.tag)
    counts = ledger.counts()
    for k, v in counts.items():
        print(f"  {k}: {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
