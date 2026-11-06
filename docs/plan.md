# Execution plan (re-baselined Fri 2026-11-06 IST)

Deadline: **Thu 12 Nov 2026, 12:00 PST = Fri 13 Nov ~01:30 IST.** Internal
target: Devpost submitted by **Thu 12 Nov ~10:00 IST** (≈ 7 h buffer).

## Today (Fri 6): scaffold + spikes -> **G-SPIKE DELIVERED**

* scaffold committed; spikes 0-4 run through 3j (17 runs, ~90 receipts in runs/)
* invoice family verified end-to-end (create -> record_payment -> record_refund);
  order money path closed on the default payee (SF-2) -> fallback pre-decided
* 8 measured findings (SF-1..SF-8) in docs/evidence.md; headline: SF-5
  (mis-keyed money field silently stored as $0 invoice)
* MCP stdio snapshot: 28 tools, record_* tools absent (SF-8)
* spike4 remaining item: remote /http transport comparison (optional, Sat)

## User-side tasks (block gate decisions, not the scaffold)

1. **developer.paypal.com** -> sign in (auto-creates default Business + Personal
   sandbox accounts) -> Apps & Credentials -> Sandbox tab -> copy Client ID/Secret
   into `.env`.
2. DONE 2026-11-06 - credentials wired; fresh token minted for spike 4.
3. DONE 2026-11-06 - card path closed by the payee gate (SF-2), independent of
   card region (two cards tried).
4. DONE 2026-11-06 - India-recipient block confirmed recipient-side (SF-3);
   sends verified to an RFC-2606 placeholder address. Optional: a US-country
   Personal sandbox account would resume the realistic send lifecycle.
5. **Check the employer contract** for outside-work/IP clauses - the rules require
   sole ownership. GO/NO-GO gate for submission.
6. Join the hackathon on Devpost and create the draft submission now (points form
   fields out early; the Nov-5 early-review offer has passed).
7. Ask organisers via the community channel: do sandbox MCP-behaviour findings
   count for "Best Use of PayPal + AI"? (report F-question 2).

## Gate schedule (IST), slip-adjusted from E7

| Day | Work | Gate |
|---|---|---|
| Fri 6 | scaffold + spikes 0-3 (+ spike4 if node exists) | G-SPIKE: money path or invoice-only slice |
| Sat 7 | harness pass 1 over the matrix (pruned cells, receipts) | coverage baseline **DONE**: pass1 (verdict plumbing bug found in its own receipts, superseded), pass1b (extractor fixed), pass1c clean 37/39 REST + 12/12 MCP; cells 16/17 transient network resets re-executed in pass1c-fx; SF-9/SF-10 surfaced |
| Sun 8 | pass 1.1 fixes; doc-vs-sandbox deltas table (the atlas) | atlas v0 **DONE**: ledger re-keyed to per-(cell,transport) rows (the dual-transport data loss found in pass1/1b/1c); canonical rerun `pass1d2` = 51/51 REST + 12/12 MCP, PASS 29/DRIFT 10/OBSERVE 24; `atlas/atlas_v0.md+json` builds D-1..D-8 out of receipts + spike4b closes unknown E (remote /http 404, /sse silent) |
| Mon 9 | state model + BFS depth<=6; first counterexample | G-FINDING **DONE (replayable route)**: `scripts/replay_findings.py` re-executes SF-5/SF-1x/SF-10/SF-9 live, 4/4 REPLAYED receipted; BFS-depth search dropped with documented not-scheduled reason (its net-new abusive sequences are already covered by the four abuse classes + replay artifacts; the spend went to the Tue cycle instead) |
| Tue 10 | LLM policy compile + repair loop + replay + HTML report | **feature freeze**: `asa/policy.py` engine; `policies/compiled/*_v0.json` FAIL with receipted counterexamples -> `*_v1.json` receipt-repaired (PASS / standing-upstream-fail documented); `report/index.html` single offline file; README + Devpost text frozen |
| Wed 11 | clean full rerun (seeded, logged), README polish, record + upload video, Devpost text | video done (Human task); optional `--tag final` rerun if the deadline allows |
| Thu 12 | submit by ~10:00 IST | submitted |

Fallback chain, pre-decided:
* capture path dead -> invoice-only slice (spike 3 carries money semantics);
* no counterexample within bounds -> atlas + honest negative result; demo lane =
  Best Demo Delivery (audit harness run recorded); P stays a lab tool with receipts;
* remote MCP auth fails -> stdio transport only; keep the diff as a documented finding.

## Prize-lane targeting (from verified rules §8)

* Primary: **Best Use of PayPal + AI** ($5k) - audit harness over PayPal's own
  MCP/toolkit surface + LLM policy compile/repair. Name PayPal and AI in the
  description, Built With, and the video (per the Devpost update's advice).
* Secondary: **Best Demo Delivery** ($5k) - judges must be able to run something:
  `python scripts/...` with clear sandbox run instructions + a seeded HTML report.
* Not targeted: sponsor lanes (no product fit), Most Creative.

## Submission checklist (rule-mapped)

- [ ] public repo, MIT LICENSE at top (visible in About)
- [ ] text description: features, functionality, what was newly built
- [ ] run instructions complete enough for judges to build and run (functional
      demo via repo instructions - no hosting needed)
- [ ] tools/models disclosure: which model compiled policies, how AI is used
- [ ] video < 3 min, YouTube public, project running on target device, no
      third-party music/trademarks
- [ ] keep working/build available until the Judging Period ends Dec 15
- [ ] keep the idea confidential until submission
