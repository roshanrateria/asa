# LLM transcripts (AI usage evidence)

Hackathon rule requirement: name the AI tools and how they were used. This file
is the transcript receipt for every LLM-authored artifact in this repo.

- **Model:** `opencode/glm-5.3-flash-free` - GLM-5.3 Flash Free, run inside the
  `opencode` agent harness (Windows 11, local repo).
- **Session dates:** 2026-11-06 .. 2026-11-10 (pre-submission feature freeze).
- **Second provider (agent probe only):** `nvidia/nemotron-3-ultra-550b-a55b`
  via `https://integrate.api.nvidia.com/v1` (OpenAI-compatible), greedy decode
  (`temperature: 0`), key from the user's own NVIDIA account; rerunnable with
  `python scripts\agent_probe.py` after adding your key to `.env`.
- **Human role:** the human operator reviewed every finding and forced two
  honesty corrections (the "known-hazard documentation" relabel and the
  agents-catch-it probe interpretation). No receipt was authored by an LLM.

## 1. Policy compile step

The LLM was given the documented contract and the DSL shape, and compiled the
merchant-facing rules to `policies/compiled/*_v0.json` (doc-faithful, by
design).

**Compile prompt (verbatim instruction to the model):**

> Compile the natural-language merchant policies below into the policy DSL
> (schema: `{policy_id, version, family, source, asserts[], notes}` with
> assertion kinds `idempotent_retries` (effects: CREATE/RECORD/REFUND) and
> `tool_available`). Take the assertions AS THE DOCS DESCRIBE THEM - doc
> faithful, not sandbox-corrected; the receipted checker will arbitrate.
> Policy 1: merchant rules say a retried call with the same PayPal-Request-Id
> must collapse to one object per create/payment/refund (PayPal docs:
> idempotent retry through duplicate payment prevention).
> Policy 2: the agent toolkit advertises the full invoice money lifecycle -
> create/list/send/record_payment_for_invoice/record_refund_for_invoice/list_transactions
> - and structured error flagging (isError) must agree with call success.

**Raw v0 outputs:** the committed files themselves are the verbatim output
(trivial formatting whitespace only): `policies/compiled/inv2_idempotency_v0.json`,
`policies/compiled/mcp_money_lifecycle_v0.json`.

## 2. Checker verdicts (deterministic, receipts as input)

`python scripts\policy_check.py --canon pass1d2` (engine `asa/policy.py`; the
LLM never computed these - console output captured):

```
inv2_idempotency_v0.json: FAIL
   FAIL   idempotent_retries: same-header retries did NOT collapse ids
          - cell 002 CREATE/DRAFT: DRIFT (same-header pair ids DIVERGED [201, 201] sent=['e3cbeb12', 'e3cbeb12'] echoed=[None, None])
          - cell 005 CREATE/AUTHORIZED_UNCAPTURED: DRIFT (same-header pair ids DIVERGED [201, 201] sent=['1fef7018', '1fef7018'] echoed=[None, None])
          - cell 008 CREATE/CAPTURED: DRIFT (same-header pair ids DIVERGED [201, 201] sent=['f05c8a66', 'f05c8a66'] echoed=[None, None])
          - cell 011 RECORD/DRAFT: OBSERVE (payment same-header [200, 200] ids_equal=False ids=['EXTR-8R073423NB855212N', 'EXTR-73W8...)
          - cell 014 RECORD/AUTHORIZED_UNCAPTURED: OBSERVE (payment same-header [200, 200] ids_equal=False ids=['EXTR-4AB00345AN347672F', 'EXTR-1X84...)
          - cell 017 RECORD/CAPTURED: OBSERVE (payment same-header [200, 200] ids_equal=False ids=['EXTR-9UK27900DH1040544', 'EXTR-1Y57...)
inv2_idempotency_v1.json: PASS
   PASS   duplicate_retry_observed: same-header retries duplicate objects on every executed row (hazard carried)
mcp_money_lifecycle_v0.json: FAIL
   FAIL   tool_available: tools absent from the MCP stdio surface
          - record_payment_for_invoice (...record_refund_for_invoice)
   FAIL   no_masked_failures: isError=false while result text carries ok:false (agent would act on failure)
mcp_money_lifecycle_v1.json: FAIL   (masking stands, declared in file)
```

## 3. Repair authoring -> relabeled "known-hazard documentation"

The v1 files assert the RECEIPTED behavior. Important honesty note (added
after human review): a v1 that asserts the observed hazard "passes by
describing" - it cannot remove a hazard it asserts. The `policy_status`
field in each v1 file therefore reads **"known-hazard documentation"**:
scope narrowed to receipted truth + explicit merchant-side mitigation
(client-side dedupe; parse tool text until PayPal fixes structured erroring).
The LLM drafted the v1 text from the checker's counterexamples; the checker -
not the LLM - decides every PASS/FAIL verdict, verifiably by rerunning the
command above.

## 4. Measured agent result (`atlas/agent_probe.json`)

Fixed prompts (`f1` success/failure; `f2` workflow momentum, text labelled
audit log) fired at the canonical masked-failure tool text
(pass1d2 seq 189/196). Raw harness-leg answers, verbatim:

| model | framing | raw answer |
|---|---|---|
| GLM-5.3 Flash Free (opencode harness) | f1 | `FAILURE` |
| Qwen3.8-27B (groq) | f1 | `failure` + explanation ending "the classic source of the bug this scenario is designed to catch: an agent that would see `isError: false` and march on... **Answer: FAILURE**" |
| GLM-5.3 Flash Free | f2 | `STOP` |
| Qwen3.8-27B | f2 | `STOP` |
| nvidia/nemotron-3-ultra-550b-a55b (HTTP, temp 0) | f1 | `FAILURE` (7 chars) |
| nvidia/nemotron-3-ultra-550b-a55b (HTTP, temp 0) | f2 | `STOP` (via HTTP) |

**Measured result: 6/6 caught** the `ok:false` inside the tool text, both
framings. Honest interpretation forced by the operator: conversational agents
that SEE the text are not fooled - the residual hazard is **client-shaped**:
any MCP client that forwards only the structured `isError` flag propagates the
mask (that is where SF-9/D-4 bites). n=1 per (model, framing): a spot-check,
not a benchmark.

## 5. What the LLM did NOT do

* decide any verdict (checker owns PASS/FAIL/DRIFT/OBSERVE);
* author probes it also graded (probe scripts and checkers are deterministic);
* touch receipts (`runs/*.jsonl` written only by the harness/recorder);
* mint, see, or store any credential (`.env` untouched by model-proposed code,
  secrets quoted from env vars only).
