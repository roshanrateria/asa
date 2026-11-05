# Coverage pass1b (2026-11-07)

counts: {"total_cells": 108, "scheduled_rest": 39, "executed_rest": 39, "scheduled_mcp": 12, "executed_mcp": 12, "not_scheduled": {"single-shape-pass-v0 (non-DUPLICATE abuse, FRESH only)": 54, "echo-refund: refund body has no text field on REST": 3, "mcp-shape-merge: one aggregate retry per cluster": 6, "mcp-tool-absent: SF-8 (record/refund not exposed by MCP)": 33}, "verdicts": {"PASS": 29, "DRIFT": 7, "OBSERVE": 15}}

## Not-scheduled reasons

- `  3` cells — echo-refund: refund body has no text field on REST (e.g. [100, 103, 106])
- `  6` cells — mcp-shape-merge: one aggregate retry per cluster (e.g. [2, 3, 5, 6, 8])
- ` 33` cells — mcp-tool-absent: SF-8 (record/refund not exposed by MCP) (e.g. [10, 11, 12, 13, 14])
- ` 54` cells — single-shape-pass-v0 (non-DUPLICATE abuse, FRESH only) (e.g. [29, 30, 32, 33, 35])

## Executed rows

| cell | transport | status chain | verdict | note |
|---|---|---|---|---|
| 001 | mcp-stdio | 200 | PASS | mcp create ids=['INV2-LMSX-RFTS-24GB-MCPD'] ok=True |
| 002 | rest | 201,201 | DRIFT | same-header pair ids DIVERGED [201, 201] |
| 003 | rest | 201,201 | PASS | no-header pair ids duplicated (documented hazard) [201, 201] |
| 004 | mcp-stdio | 200 | PASS | mcp create ids=['INV2-E87Q-6KG8-2U24-9KHK'] ok=True |
| 005 | rest | 201,201 | DRIFT | same-header pair ids DIVERGED [201, 201] |
| 006 | rest | 201,201 | PASS | no-header pair ids duplicated (documented hazard) [201, 201] |
| 007 | mcp-stdio | 200 | PASS | mcp create ids=['INV2-GL4H-R36X-8SGZ-3SHW'] ok=True |
| 008 | rest | 201,201 | DRIFT | same-header pair ids DIVERGED [201, 201] |
| 009 | rest | 201,201 | PASS | no-header pair ids duplicated (documented hazard) [201, 201] |
| 010 | rest | 200 | PASS | payment fresh [200] |
| 011 | rest | 200,200 | OBSERVE | payment same-header [200, 200] ids_equal=False ids=['EXTR-4FD249128T661952G', 'EXTR-6N428923AM584154E'] |
| 012 | rest | 200,200 | PASS | payment no-header [200, 200] two_money_effects=True ids=['EXTR-4B538200NE324030M', 'EXTR-7CT95678T8281235H'] |
| 013 | rest | 200 | PASS | payment fresh [200] |
| 014 | rest | 200,200 | OBSERVE | payment same-header [200, 200] ids_equal=False ids=['EXTR-6AP00317KS2005325', 'EXTR-7YD0099042310720C'] |
| 015 | rest | 200,200 | PASS | payment no-header [200, 200] two_money_effects=True ids=['EXTR-7ST472237S0854015', 'EXTR-2HY269822X071121S'] |
| 016 | rest | 200 | PASS | payment fresh [200] |
| 017 | rest | 200,200 | OBSERVE | payment same-header [200, 200] ids_equal=False ids=['EXTR-1C7203219H987021G', 'EXTR-2Y112068SS9137324'] |
| 018 | rest | 200,200 | PASS | payment no-header [200, 200] two_money_effects=True ids=['EXTR-9DD86241C0402770W', 'EXTR-041164411T291243L'] |
| 019 | rest | 422 | PASS | refund fresh on unpaid [422] issue=CANNOT_PROCESS_REFUNDS (expect 4xx: unpaid wires have no refundable money) |
| 020 | rest | 422,422 | OBSERVE | refund same-header [422, 422] ids_equal=True ids=['INV2-3DQ9-H52Y-75KP-7Y26', 'INV2-3DQ9-H52Y-75KP-7Y26'] |
| 021 | rest | 422,422 | OBSERVE | refund no-header [422, 422] distinct_refund_ids=1 ids=['INV2-FPE2-MHLG-8YJW-UC2P', 'INV2-FPE2-MHLG-8YJW-UC2P'] |
| 022 | rest | 422 | PASS | refund fresh on unpaid [422] issue=CANNOT_PROCESS_REFUNDS (expect 4xx: unpaid wires have no refundable money) |
| 023 | rest | 422,422 | OBSERVE | refund same-header [422, 422] ids_equal=True ids=['INV2-Y53Y-BHCY-6ZB4-SYBB', 'INV2-Y53Y-BHCY-6ZB4-SYBB'] |
| 024 | rest | 422,422 | OBSERVE | refund no-header [422, 422] distinct_refund_ids=1 ids=['INV2-F8Q9-39T3-AAF4-E7HQ', 'INV2-F8Q9-39T3-AAF4-E7HQ'] |
| 025 | rest | 200 | PASS | refund fresh on paid [200] |
| 026 | rest | 200,200 | OBSERVE | refund same-header [200, 200] ids_equal=False ids=['EXTR-8GW96114E2881535L', 'EXTR-66150756R5953005R'] |
| 027 | rest | 200,200 | OBSERVE | refund no-header [200, 200] distinct_refund_ids=2 ids=['EXTR-4YG496699M227332S', 'EXTR-5J6163836M354635G'] |
| 028 | mcp-stdio | 200 | PASS | mcp create ids=['INV2-Z67H-2TA6-XUFD-MXY3'] ok=True |
| 031 | mcp-stdio | 200 | PASS | mcp create ids=['INV2-FYZL-3ER8-HUEF-QLSL'] ok=True |
| 034 | mcp-stdio | 200 | PASS | mcp create ids=['INV2-P3Z8-LQQV-HR3Q-8ZQA'] ok=True |
| 037 | rest | 200 | PASS | pay on DRAFT money=[200] (allowed-by-design) |
| 040 | rest | 200 | PASS | pay on AUTHORIZED_UNCAPTURED money=[200] (allowed-by-design) |
| 043 | rest | 422 | PASS | pay over remaining amount [422] issue=PAYMENT_AMOUNT_GREATER_THAN_AMOUNT_DUE |
| 046 | rest | 422 | PASS | refund on unpaid DRAFT invoice [422] issue=CANNOT_PROCESS_REFUNDS |
| 049 | rest | 422 | PASS | refund on unpaid AUTHORIZED_UNCAPTURED invoice [422] issue=CANNOT_PROCESS_REFUNDS |
| 052 | rest | 200 | PASS | refund within paid [200] |
| 055 | mcp-stdio | 200 | PASS | mcp create ids=['INV2-XP6D-GKLE-9WAC-THPW'] ok=True |
| 058 | mcp-stdio | 200 | PASS | mcp create ids=['INV2-QBJM-FWU4-XF3P-BDVD'] ok=True |
| 061 | mcp-stdio | 200 | PASS | mcp create ids=['INV2-AZTH-WW8Y-Q895-95FQ'] ok=True |
| 064 | rest | 200,200,200 | OBSERVE | cumulative boundary profile x-x-x |
| 067 | rest | 200,200,200 | OBSERVE | cumulative boundary profile x-x-x |
| 070 | rest | 200,200,200 | OBSERVE | cumulative boundary profile x-x-x |
| 073 | rest | 422,422,422 | OBSERVE | cumulative boundary profile 422-422-422 |
| 076 | rest | 422,422,422 | OBSERVE | cumulative boundary profile 422-422-422 |
| 079 | rest | 200,200,422 | OBSERVE | cumulative boundary profile x-x-422 |
| 082 | mcp-stdio | 200 | DRIFT | mcp MASKED-FAILURE: isError=false but text ok:false (texts sample: {"ok":false,"status":406,"code":"PAYPAL_API |
| 085 | mcp-stdio | 200 | DRIFT | mcp create ids=['INV2-2K2M-5NWG-S9TD-TVS3'] ok=True echo=reflected-verbatim |
| 088 | mcp-stdio | 200 | DRIFT | mcp MASKED-FAILURE: isError=false but text ok:false (texts sample: {"ok":false,"status":406,"code":"PAYPAL_API |
| 091 | rest | 200 | PASS | echo-in-payment-note [200] |
| 094 | rest | 403 | DRIFT | echo-in-payment-note [403] |
| 097 | rest | 200 | PASS | echo-in-payment-note [200] |
