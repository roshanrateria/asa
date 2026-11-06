# Video script - asa (Agent Surface Audit)

Target: **<= 2:50**, YouTube **Public**, shows the project running on this
machine (Windows laptop), **no third-party music, no trademarks on screen,
no `.env`, no tokens ever visible**. One live terminal command + one report
scroll + one closer.

---

## Shot list

### Shot 0 - Staging (record BEFORE hitting rec; see checklist below)

Nothing on screen but: a **fresh terminal** in the repo root at a large
font, and one browser tab about to open `report/index.html`. Everything
else closed.

### Shot 1 - Hook over the live replay (0:00 - 0:20)

Action: type and run

```
.venv\Scripts\python scripts\replay_findings.py
```

Narration (over the running output):

> "This is a black-box audit of PayPal's *agent* surface - the official
> @paypal/mcp server plus the invoice REST family. Everything you see runs
> in the sandbox, right now, and leaves a JSONL receipt."

While `[R1]` prints:

> "Here I create an invoice with the WRONG field key - `line_items` instead
> of `items`. PayPal returns 201 Created... and the invoice is worth
> $0.00. No error. Anywhere."

While `[R2]` prints:

> "Retry the same call with the same idempotency header - invoicing
> ignores the header completely. One header, two real invoices."

### Shot 2 - The mask (0:20 - 0:45)

Point (do not zoom, just let the lines print) at `[R4]`:

> "And the worst one: the MCP tool reports `isError=false` - success. But
> the failure is hiding inside the text: `ok false, status 406`. Any agent
> that trusts the structured flag acts on an invoice that was never
> written. That masking pattern shows up twice in our receipts - API class
> and schema class."

As the run finishes:

> "Four findings, replayed four for four, live."

### Shot 3 - Report scroll (0:45 - 1:45)

Action: switch to the browser tab, refresh `report/index.html`, scroll
slowly and stop at each section.

1. Top KPIs (counts: 51 REST + 12 MCP executed cells).
   Narration: "The report is built only from our own receipt JSON - it
   renders what the sandbox receipts prove and labels every delta
   PASS / DRIFT / OBSERVE - we never say 'bug', we say what a mirror
   world would have to assume."
2. Delta table - stop on D-1 (idempotency ignored) and D-2 (mis-key $0).
   "Each delta cites the doc, the receipts, and a replay command."
3. Policy section - stop on the v0 FAIL row then the v1 PASS row.
   "The checker is deterministic code, not the model. The v0 policies
   fail against receipts; our v1 files are declared known-hazard
   documentation - they document the carried hazard, they don't claim to
   fix it."
4. Measured agent table - stop on the Wilson row.
   "We measured the mask: same exact failure text, NVIDIA model at 20
   trials per cell, a glm cross-engine leg, 75 trials total - zero hazard
   outcomes, Wilson upper bound 0.16 at n=20. Agents who SEE the text
   catch it. What we could not test is a client that forwards only the
   flag - that stays a labeled hypothesis, and we say so."
5. Miskey verdict line.
   "Bonus: the MCP tool's schema actually enforces `items` - it rejects
   the mis-keyed body... and it reports that rejection as success too.
   Second independent instance of the mask."

### Shot 4 - Closer (1:45 - 2:20)

Browser still on the report, terminal visible in background if room.
Narration:

> "Sandbox-only by construction - the config hard-refuses anything that
> is not sandbox. Clone it, paste your sandbox creds, and replay all four
> findings live in under a minute. asa - Agent Surface Audit. The link
> and the receipts are in the repo."

On-screen text (add in editor, not on desktop): repo URL
`github.com/roshanrateria/asa`.

### Off-mic safety line (record but do not plan to use)

> "The sandbox occasionally rate-limits; those receipts came from the
> same script this morning" (only if a live call fails mid-take - then
> just roll Shot 3 backups below).

### Backup footage (record separately, use only if the live run glitches)

- `runs/replay-findings.jsonl` tail in VS Code showing `[R1..R4]` verdicts.
- The committed `report/index.html` already contains everything - Shot 3
  can carry the whole video if needed.

---

## Pre-record staging checklist

- [ ] Close **every** app that has ever shown secrets: editors with `.env`,
      any token in clipboard-history, browser tabs with dev portals,
      NVIDIA playground sessions.
- [ ] `C:\Users\rater\Downloads\asa-clone-test\` (contains a copy of
      creds for the clean-clone test): **do not open it during recording**;
      delete it after the video.
- [ ] Fresh Windows Terminal: `cd C:\Users\rater\Downloads\paypal-ai`,
      font size ~16, run `clear`, type the replay command but do NOT press
      enter; pause breathing room.
- [ ] Browser: ONE tab only - open `about:blank`, then a second tab to
      `file:///C:/Users/rater/Downloads/paypal-ai/report/index.html`,
      fullscreen/zoom ~110%. Scroll once to verify before recording.
- [ ] Notifications OFF (`Win + F`... easier: enable Focus assist / do-not-
      disturb), taskbar auto-hidden, clock fine (it stamps - that's OK).
- [ ] Recorder: Xbox Game Bar (`Win + Alt + R`) at full screen or OBS
      1920x1080 @30fps on the main display; test 10 seconds and play it
      back to check audio level before the real take.
- [ ] Microphone test phrase, 1 metre distance, no fan/keyboard noise in
      the first take; do the typing between sentences, not during.
- [ ] No music, no logos: close every app; nothing trademarked on screen
      (Windows desktop + this project only).
- [ ] Rehearse the full run once with a stopwatch - it should land ~2:20
      leaving trim headroom.
- [ ] After the take: verify the video shows zero moments where a path
      like `asa-clone-test` or any `.env` scroll could be readable.

## Post-record checklist

- [ ] Publish on YouTube as **Public**, title suggestion:
      `asa - black-box audit of PayPal's agent surface (sandbox only)`,
      description: repo link + the four replayed findings + license MIT.
- [ ] Put the YouTube link on Devpost, register/check the draft entry,
      deadline **Thu 12 Nov 12:00 PST**.
- [ ] Delete `C:\Users\rater\Downloads\asa-clone-test\` (it holds a copy
      of credentials).
- [ ] Final freeze: re-run the clean-clone judge test once after the last
      push (records 4/4 REPLAYED + identical policy verdicts).
