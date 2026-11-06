"""HTML report builder (Tue 2026-11-10, feature-freeze artifact).

Reads the receipt-derived JSON artifacts and emits ONE static, offline file:
  report/index.html

Inputs (all written by earlier scripts in this repo - the report renders,
it never re-derives):
  atlas/atlas_v0.json          deltas + counts + echo matrix   (build_atlas.py)
  atlas/policy_check.json      compiled-policy verdicts          (policy_check.py)
  atlas/replay_findings.json   live replay verdicts              (replay_findings.py)

No external assets, no CDN, no JS beyond none - safe to attach to a Devpost
submission and to open offline by judges.
"""

from __future__ import annotations

import html
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas"
OUT = ROOT / "report" / "index.html"


def _fmt_error(s: str) -> str:
    return f'<span class="verdict v{html.escape(str(s))}">{html.escape(str(s))}</span>'


def main() -> int:
    atlas = json.loads((ATLAS / "atlas_v0.json").read_text(encoding="utf-8"))

    def maybe(name: str) -> dict | None:
        p = ATLAS / name
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None

    policy = maybe("policy_check.json")
    replay = maybe("replay_findings.json")

    counts = atlas.get("counts_canon_plus_aux", {})
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    deltas = atlas.get("deltas", [])
    exercised = [d for d in deltas if not d["status"].startswith("NOT EXERCISED")]

    css = """
    :root { --ink:#0f172a; --muted:#64748b; --line:#e2e8f0; --bg:#f8fafc;
            --pass:#047857; --drift:#b45309; --obs:#4338ca; --fail:#b91c1c; }
    * { box-sizing:border-box; }
    body { font: 15px/1.5 system-ui,-apple-system,'Segoe UI',sans-serif;
           color:var(--ink); background:var(--bg); margin:0; }
    main { max-width:1040px; margin:0 auto; padding:28px 20px 64px; }
    h1 { font-size:26px; margin:0 0 4px; }
    h2 { font-size:18px; margin:34px 0 8px; padding-bottom:4px;
         border-bottom:1px solid var(--line); }
    .sub { color:var(--muted); font-size:13.5px; }
    .kpi { display:inline-block; background:#fff; border:1px solid var(--line);
           border-radius:10px; padding:10px 16px; margin:14px 10px 0 0;
           font-size:14px; }
    .kpi b { font-size:20px; display:block; }
    table { border-collapse:collapse; width:100%; background:#fff;
            border:1px solid var(--line); border-radius:8px; font-size:13.5px; }
    th { text-align:left; background:#f1f5f9; padding:7px 9px;
         border-bottom:1px solid var(--line); font-weight:600; }
    td { padding:6px 9px; border-bottom:1px solid var(--line);
         vertical-align:top; }
    tr:last-child td { border-bottom:0; }
    code, pre { font-family:ui-monospace,Consolas,monospace; font-size:12.5px; }
    pre { background:#0f172a; color:#e2e8f0; padding:12px 14px;
          border-radius:8px; overflow:auto; }
    .verdict { font-weight:700; }
    .vPASS { color:var(--pass); } .vDRIFT,.vFAIL { color:var(--drift); }
    .vOBSERVE,.vOPEN { color:var(--obs); } .vREPLAYED { color:var(--pass); }
    .vCHANGED { color:var(--fail); }
    li { margin:3px 0; }
    .foot { color:var(--muted); font-size:12.5px; margin-top:40px;
            border-top:1px solid var(--line); padding-top:10px; }
    """

    canon_p = atlas.get("canonical_pass") or "?"
    aux_p = atlas.get("aux_pass")
    kpis = "".join([
        f"<span class='kpi'><b>{counts.get('total_cells', '?')}</b>candidate cells</span>",
        f"<span class='kpi'><b>{counts.get('executed_rest', '?')}</b>REST executed</span>",
        f"<span class='kpi'><b>{counts.get('executed_mcp', '?')}</b>MCP executed</span>",
        f"<span class='kpi'><b>{counts.get('verdicts', {}).get('DRIFT', 0)}</b>DRIFT (deltas)</span>",
        f"<span class='kpi'><b>{len(exercised)}/{len(deltas)}</b>receipted deltas (last: D-8 not exercised)</span>",
    ])

    parts = [f"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>asa - Agent Surface Audit</title><style>{css}</style></head><body><main>
<h1>Agent Surface Audit (asa)</h1>
<div class="sub">black-box audit of PayPal's agent surface (MCP @paypal/mcp + REST
invoice family), sandbox-only; every claim below cites receipts under <code>runs/</code>.
Canon pass <b>{html.escape(canon_p)}</b>{f" (aux {html.escape(aux_p)})" if aux_p else ""}
. Generated {generated}.</div>
{kpis}
"""]

    # deltas
    parts.append("<h2>Doc-vs-sandbox deltas (the atlas)</h2>")
    parts.append("<table><tr><th>id</th><th>documented expectation</th><th>observed on sandbox"
                 "</th><th>status</th><th>cites</th></tr>")
    for d in atlas.get("deltas", []):
        parts.append(
            "<tr><td><b>{id}</b></td><td>{claim}</td><td>{seen}</td>"
            "<td>{status}</td><td class='sub'>{cites}</td></tr>".format(
                id=html.escape(d["id"]), claim=html.escape(d["claim"]),
                seen=html.escape(d["seen"]), status=html.escape(d["status"]),
                cites=html.escape(d["cites"])))
    parts.append("</table>")

    # echo matrix
    parts.append("<h2>Hostile-text artifact matrix (same payload, across passes/channels)</h2>")
    parts.append("<table><tr><th>pass</th><th>cell</th><th>channel</th>"
                 "<th>status</th><th>artifact</th></tr>")
    for e in atlas.get("echo_matrix", []):
        parts.append(
            "<tr><td>{p}</td><td>{c}</td><td>{ch}</td><td>{s}</td><td>{a}</td></tr>"
            .format(p=html.escape(e["pass"]), c=html.escape(str(e["cell"])),
                    ch=html.escape(e["transport"]), s=html.escape(str(e["status"])),
                    a=html.escape(e["artifact"])))
    parts.append("</table>")

    # policy checks
    parts.append("<h2>Policy compile + repair loop (compiled policies vs receipts)</h2>")
    if policy:
        parts.append("<table><tr><th>policy</th><th>overall</th><th>assertions</th></tr>")
        for c in policy.get("checks", []):
            per = "<br>".join(
                f"{_fmt_error(a['verdict'])} {html.escape(a['kind'])} - "
                f"{html.escape(a['note'])}"
                + (f"<span class='sub'> ({html.escape(str(len(a['counterexamples'])))} "
                   f"counterexamples: {html.escape('; '.join(a['counterexamples'][:2]))})</span>"
                   if a["counterexamples"] else "")
                for a in c.get("assertions", []))
            parts.append(f"<tr><td><code>{html.escape(c['policy'])}</code></td>"
                         f"<td>{_fmt_error(c['overall'])}</td><td>{per}</td></tr>")
        parts.append("</table>")
        parts.append("<div class='sub'>The v0 policies are doc-faithful and FAIL with receipted"
                     " counterexamples; the v1 repairs are scope-shrunk to receipted behavior."
                     " That fail &rarr; repair cycle is the audit's core loop.</div>")
    else:
        parts.append("<div class='sub'>policy_check.json missing - run scripts/policy_check.py"
                     " before building the report.</div>")

    # replay
    parts.append("<h2>Replayable findings (re-executed live today)</h2>")
    if replay:
        parts.append("<table><tr><th>finding</th><th>verdict</th><th>detail</th></tr>")
        for r in replay.get("results", []):
            parts.append(
                "<tr><td><b>{f}</b> {l}</td><td>{v}</td><td class='sub'>{d}</td></tr>"
                .format(f=html.escape(r["finding"]), l=html.escape(r["label"]),
                        v=_fmt_error(r["verdict"]), d=html.escape(r["detail"])))
        parts.append("</table>")
    else:
        parts.append("<div class='sub'>replay_findings.json missing - run"
                     " scripts/replay_findings.py.</div>")

    # AI usage disclosure + measured agent result
    agents = maybe("agent_probe.json")
    parts.append("<h2>AI usage disclosure &amp; measured agent result</h2>")
    parts.append("""<div>Language model use, named per the hackathon rules:
<ul>
<li><b>Compile + repair authoring:</b> GLM-5.3 Flash Free (opencode harness) compiled
the merchant policies to <code>policies/compiled/*_v0.json</code> and drafted the
<code>*_v1.json</code> repairs - transcripts: model id, prompts, raw v0 outputs
and repair diffs at <code>docs/llm_transcripts.md</code>.</li>
<li><b>Verdicts:</b> every FAIL/PASS verdict on a policy is decided by the
deterministic checker <code>asa/policy.py</code> against receipts - the LLM never
decides (and v1 is <i>known-hazard documentation</i>, not a repair that removes
any hazard: see <code>policy_status</code> in each v1 file).</li>
<li><b>Measured agent result (<code>atlas/agent_probe.json</code>):</b> with the exact
masked-failure tool text from canonical receipts (pass1d2 seq 189/196), 3 models
&times; 2 framings - GLM-5.3 Flash Free, Qwen3.8-27B (groq),
nvidia/nemotron-3-ultra-550b-a55b (key-per-rerun reproducible) - all 6 probes
<b>caught</b> the ok:false inside the text (f1 FAILURE 3/3, f2 STOP 3/3).
Reading: conversational agents that SEE the text are not fooled; the residual
hazard is client-shaped - any MCP client that forwards only the structured
<code>isError</code> flag propagates the mask. SF-9 stands as a protocol finding.</li>
</ul></div>""")
    if agents:
        rows = "".join(
            "<tr><td>{m}</td><td>{fm}</td><td>{v}</td><td>{a}</td></tr>".format(
                m=html.escape(str(p.get("model_used") or p.get("model"))),
                fm=html.escape(str(p.get("framing", "f1"))),
                v=html.escape(str(p.get("verdict"))),
                a=html.escape(str(p.get("action", "-"))))
            for p in agents.get("probes", []))
        parts.append("<table><tr><th>model</th><th>framing</th>"
                     "<th>verdict</th><th>action</th></tr>" + rows + "</table>")
    else:
        parts.append("<div class='sub'>agent_probe.json missing - run "
                     "scripts/agent_probe.py.</div>")

    # honest exclusions
    parts.append("<h2>Honest exclusions (never silence)</h2><ul>")
    for reason, n in atlas.get("not_scheduled", {}).items():
        parts.append(f"<li><b>{n}</b> cells - {html.escape(reason)}</li>")
    parts.append("</ul>")

    # repro
    parts.append("""<h2>Reproducibility (sandbox-safe commands)</h2>
<pre>
python scripts\\harness_pass1.py --tag pass1d2     # full 108-cell matrix (REST + MCP phases)
python scripts\\fx_cells.py --tag pass1d2-fx --cells 999   # failed-cell follow-ups (if any 429/net)
python scripts\\policy_check.py --canon pass1d2    # policy compile/repair verdicts
python scripts\\replay_findings.py                 # re-execute headline findings live
python scripts\\build_atlas.py --canonical pass1d2 # this atlas's inputs (deltas JSON/MD)
python scripts\\build_report.py                    # this file
</pre>
All commands require sandbox credentials in <code>.env</code> - <code>asa/config.py</code>
hard-refuses non-sandbox environments; receipts land in <code>runs/</code>.
""")

    parts.append(f"""<div class="foot">asa (Agent Surface Audit) - lab tool, sandbox-only.
Receipts: <code>runs/</code>; ledger: <code>docs/evidence.md</code> (SF-1..SF-10);
atlas: <code>atlas/</code>. Verdicts are labelled PASS / DRIFT / OBSERVE; never
"bug" - behavior deltas vs documented contract.</div>
</main></body></html>""")

    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text("\n".join(parts), encoding="utf-8")
    print(f"REPORT: {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
