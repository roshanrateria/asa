# Coverage pass 1 (2026-11-07)

counts: {"total_cells": 108, "scheduled_rest": 39, "executed_rest": 39, "scheduled_mcp": 12, "executed_mcp": 12, "not_scheduled": {"single-shape-pass-v0 (non-DUPLICATE abuse, FRESH only)": 54, "echo-refund: refund body has no text field on REST": 3, "mcp-shape-merge: one aggregate retry per cluster": 24, "mcp-tool-absent: SF-8 (record/refund not exposed by MCP)": 72}, "verdicts": {"PASS": 27, "DRIFT": 9, "OBSERVE": 15}}

## Not-scheduled reasons

- `  3` cells — echo-refund: refund body has no text field on REST (e.g. [100, 103, 106])
- ` 24` cells — mcp-shape-merge: one aggregate retry per cluster (e.g. [2, 3, 5, 6, 8])
- ` 72` cells — mcp-tool-absent: SF-8 (record/refund not exposed by MCP) (e.g. [10, 11, 12, 13, 14])
- ` 54` cells — single-shape-pass-v0 (non-DUPLICATE abuse, FRESH only) (e.g. [29, 30, 32, 33, 35])

## Executed rows

| cell | transport | status chain | verdict | note |
|---|---|---|---|---|
| 001 | mcp-stdio | 200 | PASS | mcp create ids=['INV2-S96H-VZUD-N8QL-LZR3'] ok=True |
| 002 | rest | 201,201 | PASS | same-header pair ids collapsed [201, 201] |
| 003 | rest | 201,201 | DRIFT | no-header pair ids NOT duplicated [201, 201] |
| 004 | mcp-stdio | 200 | PASS | mcp create ids=['INV2-4C7P-88CZ-RGYV-UYDE'] ok=True |
| 005 | rest | 201,201 | PASS | same-header pair ids collapsed [201, 201] |
| 006 | rest | 201,201 | DRIFT | no-header pair ids NOT duplicated [201, 201] |
| 007 | mcp-stdio | 200 | PASS | mcp create ids=['INV2-6XQG-HESM-BAB8-973G'] ok=True |
| 008 | rest | 201,201 | PASS | same-header pair ids collapsed [201, 201] |
| 009 | rest | 201,201 | DRIFT | no-header pair ids NOT duplicated [201, 201] |
| 010 | rest | 200 | PASS | payment fresh [200] |
| 011 | rest | 200,200 | OBSERVE | payment same-header [200, 200] ids_equal=True ids=[] |
| 012 | rest | 200,200 | PASS | payment no-header [200, 200] two_money_effects=False ids=[] |
| 013 | rest | 200 | PASS | payment fresh [200] |
| 014 | rest | 200,200 | OBSERVE | payment same-header [200, 200] ids_equal=True ids=[] |
| 015 | rest | 200,200 | PASS | payment no-header [200, 200] two_money_effects=False ids=[] |
| 016 | rest | 200 | PASS | payment fresh [200] |
| 017 | rest | 200,200 | OBSERVE | payment same-header [200, 200] ids_equal=True ids=[] |
| 018 | rest | 200,200 | PASS | payment no-header [200, 200] two_money_effects=False ids=[] |
| 019 | rest | 422 | DRIFT | refund fresh [422] |
| 020 | rest | 422,422 | OBSERVE | refund same-header [422, 422] ids_equal=True ids=[] |
| 021 | rest | 422,422 | OBSERVE | refund no-header [422, 422] distinct_refund_ids=0 ids=[] |
| 022 | rest | 422 | DRIFT | refund fresh [422] |
| 023 | rest | 422,422 | OBSERVE | refund same-header [422, 422] ids_equal=True ids=[] |
| 024 | rest | 422,422 | OBSERVE | refund no-header [422, 422] distinct_refund_ids=0 ids=[] |
| 025 | rest | 200 | PASS | refund fresh [200] |
| 026 | rest | 200,200 | OBSERVE | refund same-header [200, 200] ids_equal=False ids=['EXTR-6B803622YU072163F', 'EXTR-6SD80078VN371654K'] |
| 027 | rest | 200,200 | OBSERVE | refund no-header [200, 200] distinct_refund_ids=2 ids=['EXTR-9SU26974VA9025808', 'EXTR-0KH53782H6119754R'] |
| 028 | mcp-stdio | 200 | PASS | mcp create ids=['INV2-GMDV-7ATK-GFG5-EG32'] ok=True |
| 031 | mcp-stdio | 200 | PASS | mcp create ids=['INV2-5UT6-9PQR-62R3-DEFV'] ok=True |
| 034 | mcp-stdio | 200 | PASS | mcp create ids=['INV2-A394-F8L4-YQQ7-354S'] ok=True |
| 037 | rest | 200 | PASS | pay on DRAFT money=[200] (allowed-by-design) |
| 040 | rest | 200 | PASS | pay on AUTHORIZED_UNCAPTURED money=[200] (allowed-by-design) |
| 043 | rest | 422 | PASS | pay over remaining amount [422] issue=PAYMENT_AMOUNT_GREATER_THAN_AMOUNT_DUE |
| 046 | rest | 422 | PASS | refund on unpaid DRAFT invoice [422] issue=CANNOT_PROCESS_REFUNDS |
| 049 | rest | 422 | PASS | refund on unpaid AUTHORIZED_UNCAPTURED invoice [422] issue=CANNOT_PROCESS_REFUNDS |
| 052 | rest | 200 | PASS | refund within paid [200] |
| 055 | mcp-stdio | 200 | PASS | mcp create ids=['INV2-G6DX-UWH8-4U3A-PY96'] ok=True |
| 058 | mcp-stdio | 200 | PASS | mcp create ids=['INV2-ZMUY-K68A-RGUN-M32A'] ok=True |
| 061 | mcp-stdio | 200 | PASS | mcp create ids=['INV2-786U-EJE6-9YY4-ZPWM'] ok=True |
| 064 | rest | 200,200,200 | OBSERVE | cumulative boundary profile x-x-x |
| 067 | rest | 200,200,200 | OBSERVE | cumulative boundary profile x-x-x |
| 070 | rest | 200,200,200 | OBSERVE | cumulative boundary profile x-x-x |
| 073 | rest | 422,422,422 | OBSERVE | cumulative boundary profile 422-422-422 |
| 076 | rest | 422,422,422 | OBSERVE | cumulative boundary profile 422-422-422 |
| 079 | rest | 200,200,422 | OBSERVE | cumulative boundary profile x-x-422 |
| 082 | mcp-stdio | 200 | DRIFT | mcp create ids=[] ok=True |
| 085 | mcp-stdio | 200 | DRIFT | mcp create ids=['INV2-88KQ-SJ2N-WVZD-3Z74'] ok=True echo=reflected-verbatim |
| 088 | mcp-stdio | 200 | DRIFT | mcp create ids=[] ok=True |
| 091 | rest | 200 | PASS | echo-in-payment-note [200] |
| 094 | rest | 406 | DRIFT | echo-in-payment-note [406] |
| 097 | rest | 200 | PASS | echo-in-payment-note [200] |
