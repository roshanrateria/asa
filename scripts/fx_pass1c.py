"""pass1c follow-up (2026-11-06): re-execute cells 16/17 after transient
network setup failures (WinError 10054 / 10060 mid-run, run otherwise clean).

Only the REST phase for exactly these two cells; tag 'pass1c-fx' so receipts
and atlas stay separate. Everything else reuses the pass-1c artifact.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from asa import probe
from asa.config import load_config
from asa.matrix import candidate_grid
from asa.recorder import Recorder
from scripts.harness_pass1 import write_reports


def main() -> int:
    cfg = load_config()
    rec = Recorder(cfg.runs_dir, "harness-pass1c-fx")
    cells = [c for c in candidate_grid() if c.cell_id in (16, 17)]
    ledger = probe.Ledger(total=len(cells))
    print(f"pass1c-fx: re-running cells {[c.cell_id for c in cells]}")
    probe.run_rest_phase(cfg, cells, ledger, rec)
    write_reports(ledger, "pass1c-fx")
    counts = ledger.counts()
    for k, v in counts.items():
        print(f"  {k}: {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
