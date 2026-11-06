# Agent Surface Audit (`asa`)

Black-box audit of **PayPal's own agent surface** - the official Agent Toolkit
and MCP server - measured against their **sandbox** behaviour, with an LLM
compiling merchant policies into a small DSL that a deterministic checker
confronts with the receipts.

Built for the PayPal AI Hackathon ("Build What's Next with PayPal and AI",
deadline Thu 12 Nov 2026, 12:00 PST). Sandbox only, by construction.

**Judge entry points:** the one-file audit is `report/index.html`
(offline, renders only what receipts prove); committed sanitized evidence
lives in `atlas/sample_receipts/`; AI usage is named and bounded in
`docs/llm_transcripts.md`; the submission text draft is `docs/devpost.md`.

## Why

Merchants are handing agents refund and payment powers. The existing answers
are runtime guards (policy proxies) or generic verifiers. What nobody has
published, to our knowledge as of 2026-11-01, is a **measured behaviour model**
of PayPal's own agent tools on the sandbox: what a duplicate call actually
does, which illegal states are actually accepted, how a cumulative
over-limit sequence behaves, what untrusted text through supported fields
does. asa probes first with receipts on every call, and never enforces at
runtime - it is an audit tool for teams before they ship agents.

Status: **audit complete over the invoice anchor**. Spike day verified the
invoice family end-to-end (create -> record_payment -> record_refund) and
catalogued SF-1..SF-8 with receipts; the 108-candidate matrix then ran to a
receipt-clean canonical pass (96 candidates excluded with a receipted reason
each; 51 REST + 12 MCP executed; PASS / DRIFT / OBSERVE under `atlas/`),
adding SF-9 (MCP masks application failure as success) and SF-10
(hostile-text handling splits across artifacts). Headline finding SF-5
(silent drop -> $0 invoice) is replayable live via `scripts/replay_findings.py`.

## What AI does (and does not do)

* compile natural-language merchant policy -> schema-validated DSL
  (v0 artifacts under `policies/compiled/`, doc-faithful by design),
* draft the v1 rewrites from the checker's receipted counterexamples -
  v1 files are declared `policy_status: known-hazard documentation` (they
  document the carried hazard and its merchant-side mitigation; they do not
  remove it),
* a **deterministic checker** (`asa/policy.py` + `scripts/policy_check.py`)
  decides every PASS/FAIL against receipts - the LLM never decides,
* **measured agent result** (`atlas/agent_probe.json`, rerunnable via
  `scripts/agent_probe.py` + `scripts/merge_probe_harness.py`): the exact
  masked-failure tool text from the canonical receipts + the REAL
  `create_invoice` schema as a third probe cell - NVIDIA primary model at
  n=20/cell (temp 0.7) plus a glm-5.3-flash-free cross-engine leg at n=5/cell:
  **0 hazard outcomes in 75 measured trials** (per-cell Wilson 95% upper
  bound <= 0.43). Agents shown the text caught it in every measured trial;
  what is NOT demonstrated is the true exposure path (an MCP client that
  forwards only the structured flag - hypothesis, labeled as such).

## Architecture (blueprint E5)

```
targets:    REST api-m.sandbox.paypal.com | MCP @paypal/mcp (stdio, pinned)
            remote mcp.sandbox.paypal.com closed by spike4b (/http 404, /sse silent)
probes:     108 candidate cells = 4 abuse classes x 27 combos
            (3 effects x 3 preconditions x 3 call shapes); 96 excluded with
            a receipted reason each (see atlas not_scheduled buckets);
            canonical run executed 51 REST + 12 MCP, per (cell, transport)
recorder:   JSONL receipts per call (ids, debug_id, mock-header flag, ts)
model:      abstract states (order draft/authorized/captured; invoice
            draft/sent/paid/refunded) -- states are checked by compiled
            policy assertions, NOT searched (no BFS implemented)
report:     static offline HTML built only from receipt-derived artifacts
```

## Quickstart

Needs Python 3.11+. Node 18+ only for the MCP stdio spike.

```powershell
cp .env.example .env        # fill PAYPAL_CLIENT_ID / PAYPAL_CLIENT_SECRET (sandbox)
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt

# probes (receipts land in runs\, git-ignored)
.venv\Scripts\python scripts\spike0_smoke.py              # credentials + reads
.venv\Scripts\python scripts\spike1_dup_probe.py          # idempotency ground truth
.venv\Scripts\python scripts\spike2_money_path.py         # card capture gate (needs test card in .env)
.venv\Scripts\python scripts\spike3_invoice_roundtrip.py  # invoice fallback slice
.venv\Scripts\python scripts\spike4_mcp_snapshot.py       # MCP tool list (+ --remote)

# the audit itself
.venv\Scripts\python scripts\harness_pass1.py --tag pass1d2   # 108-candidate matrix (REST + MCP)
.venv\Scripts\python scripts\policy_check.py --canon pass1d2  # v0 policies fail vs receipts -> v1 hazard-documentation
.venv\Scripts\python scripts\replay_findings.py               # headline findings, live (7 bounded calls)
.venv\Scripts\python scripts\agent_probe.py                   # measured agent result (NVIDIA leg; optional key)
.venv\Scripts\python scripts\merge_probe_harness.py           # append cross-engine legs into atlas\agent_probe.json (offline)
.venv\Scripts\python scripts\miskey_mcp_check.py              # MCP items-enforcement + masked-schema-rejection receipt
.venv\Scripts\python scripts\build_atlas.py --canonical pass1d2  # delta tables
.venv\Scripts\python scripts\build_report.py                  # report\index.html (offline)
```

<details>
<summary>POSIX / bash equivalents (macOS, Linux, WSL)</summary>

```bash
cp .env.example .env          # fill PAYPAL_CLIENT_ID / PAYPAL_CLIENT_SECRET (sandbox)
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# probes (receipts land in runs/, git-ignored)
.venv/bin/python scripts/spike0_smoke.py              # credentials + reads
.venv/bin/python scripts/spike1_dup_probe.py          # idempotency ground truth
.venv/bin/python scripts/spike2_money_path.py         # card capture gate (needs test card in .env)
.venv/bin/python scripts/spike3_invoice_roundtrip.py  # invoice fallback slice
.venv/bin/python scripts/spike4_mcp_snapshot.py       # MCP tool list (+ --remote)

# the audit itself
.venv/bin/python scripts/harness_pass1.py --tag pass1d2   # 108-candidate matrix (REST + MCP)
.venv/bin/python scripts/policy_check.py --canon pass1d2  # v0 policies fail vs receipts -> v1 hazard-documentation
.venv/bin/python scripts/replay_findings.py               # headline findings, live (7 bounded calls)
.venv/bin/python scripts/agent_probe.py                   # measured agent result (NVIDIA leg; optional key)
.venv/bin/python scripts/merge_probe_harness.py           # append cross-engine legs into atlas/agent_probe.json (offline)
.venv/bin/python scripts/miskey_mcp_check.py              # MCP items-enforcement + masked-schema-rejection receipt
.venv/bin/python scripts/build_atlas.py --canonical pass1d2  # delta tables
.venv/bin/python scripts/build_report.py                  # report/index.html (offline)
```

Notes: the MCP stdio spike runs the official `@paypal/mcp` package via `npx`
(Node 18+). On Windows the exact same commands work from Git Bash with
`.venv/Scripts/python` instead of `.venv/bin/python`.
</details>

Judges: open `report/index.html` - it renders only what `runs/` receipts
prove, plus `atlas/atlas_v0.md` (same data, markdown form), with the
compiled-policy repair chain (`policies/compiled/*_v0.json` -> `*_v1.json`).

## Repo layout

```
asa/            matrix, ledger (per-cell per-transport rows), policy engine
  config.py     production guard + env (hard sandbox gate)
  matrix.py     108-cell definition, prune rules, tool targets
  recorder.py   JSONL receipts + id extraction
  rest_client.py sandbox REST + PayPal-Request-Id hooks
  mcp_client.py stdio MCP session (@paypal/mcp, version-pinnable via env)
  probe.py      matrix runner: anchor setups, retry shapes, verdicts
  policy.py     DSL v0 engine: compiled policies vs receipted canon
scripts/        spikes 0-4b, harness, fx, atlas/report builders, replay,
                agent probe, sample-receipt subset builder
policies/       compiled policies (v0 doc-faithful -> v1; v1 = known-hazard
                documentation per policy_status - the checker, not the LLM,
                owns every verdict)
docs/           evidence ledger (tagged), execution plan, submission text,
                LLM transcripts (docs/llm_transcripts.md)
atlas/          coverage passes + doc-vs-sandbox delta atlas + policy/replay
                artifacts + committed sample receipts (atlas/sample_receipts)
report/         offline single-file judge report (report/index.html)
```

Receipts: raw runs are git-ignored (`runs/`), but judges get a committed,
sanitized subset in `atlas/sample_receipts/` (tokens redacted to length
markers, sandbox buyer emails normalized) derived by
`scripts/build_sample_receipts.py`. Secret scan pre-push: `.env` was never
committed - the only historical pickaxe hit for credential names is the
env-var NAME in `.env.example`.

## Rules compliance snapshot (detail in docs/plan.md)

* newly created work, sandbox only,
* public repo + MIT licence at repo top, run instructions for judges,
* video < 3 min on YouTube, no third-party music/trademarks,
* targets lanes: Best Use of PayPal + AI, Best Demo Delivery.

## Licence

MIT - see `LICENSE`.
