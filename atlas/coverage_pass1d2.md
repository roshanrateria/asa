# Coverage pass1d2 (2026-11-07)

counts: {"total_cells": 108, "scheduled_rest": 51, "executed_rest": 51, "scheduled_mcp": 12, "executed_mcp": 12, "not_scheduled": {"single-shape-pass-v0 (non-DUPLICATE abuse, FRESH only)": 54, "echo-refund: refund body has no text field on REST": 3, "mcp-shape-merge: one aggregate retry per cluster": 6, "mcp-tool-absent: SF-8 (record/refund not exposed by MCP)": 33}, "verdicts": {"PASS": 29, "DRIFT": 10, "OBSERVE": 24}}

## Not-scheduled reasons

- `  3` cells — echo-refund: refund body has no text field on REST (e.g. [100, 103, 106])
- `  6` cells — mcp-shape-merge: one aggregate retry per cluster (e.g. [2, 3, 5, 6, 8])
- ` 33` cells — mcp-tool-absent: SF-8 (record/refund not exposed by MCP) (e.g. [10, 11, 12, 13, 14])
- ` 54` cells — single-shape-pass-v0 (non-DUPLICATE abuse, FRESH only) (e.g. [29, 30, 32, 33, 35])

## Executed rows

| cell | transport | status chain | verdict | note |
|---|---|---|---|---|
| 001 | rest | 201 | PASS | single create [201] |
| 001 | mcp-stdio | 200 | PASS | mcp create ids=['INV2-2Q4C-23F6-57GU-MQNG'] ok=True |
| 002 | rest | 201,201 | DRIFT | same-header pair ids DIVERGED [201, 201] sent=['e3cbeb12', 'e3cbeb12'] echoed=[None, None] |
| 003 | rest | 201,201 | PASS | no-header pair ids duplicated (documented hazard) [201, 201] sent=[None, None] echoed=[None, None] |
| 004 | rest | 201 | PASS | single create [201] |
| 004 | mcp-stdio | 200 | PASS | mcp create ids=['INV2-4WZP-MYP2-H3KZ-R64Y'] ok=True |
| 005 | rest | 201,201 | DRIFT | same-header pair ids DIVERGED [201, 201] sent=['1fef7018', '1fef7018'] echoed=[None, None] |
| 006 | rest | 201,201 | PASS | no-header pair ids duplicated (documented hazard) [201, 201] sent=[None, None] echoed=[None, None] |
| 007 | rest | 201 | PASS | single create [201] |
| 007 | mcp-stdio | 200 | PASS | mcp create ids=['INV2-74XE-G5AE-6ZS6-U6MF'] ok=True |
| 008 | rest | 201,201 | DRIFT | same-header pair ids DIVERGED [201, 201] sent=['f05c8a66', 'f05c8a66'] echoed=[None, None] |
| 009 | rest | 201,201 | PASS | no-header pair ids duplicated (documented hazard) [201, 201] sent=[None, None] echoed=[None, None] |
| 010 | rest | 200 | PASS | payment fresh [200] |
| 011 | rest | 200,200 | OBSERVE | payment same-header [200, 200] ids_equal=False ids=['EXTR-8R073423NB855212N', 'EXTR-73W80787HG252061F'] sent=[ |
| 012 | rest | 200,200 | OBSERVE | payment no-header [200, 200] two_money_effects=True ids=['EXTR-0NC82277FY270405H', 'EXTR-99330764RG069000W'] s |
| 013 | rest | 200 | PASS | payment fresh [200] |
| 014 | rest | 200,200 | OBSERVE | payment same-header [200, 200] ids_equal=False ids=['EXTR-4AB00345AN347672F', 'EXTR-1X845156M2210424U'] sent=[ |
| 015 | rest | 200,200 | OBSERVE | payment no-header [200, 200] two_money_effects=True ids=['EXTR-8TF90178165376318', 'EXTR-8E1813564N217133L'] s |
| 016 | rest | 200 | PASS | payment fresh [200] |
| 017 | rest | 200,200 | OBSERVE | payment same-header [200, 200] ids_equal=False ids=['EXTR-9UK27900DH1040544', 'EXTR-1Y572143EC3233108'] sent=[ |
| 018 | rest | 200,200 | OBSERVE | payment no-header [200, 200] two_money_effects=True ids=['EXTR-6ET88839R27430140', 'EXTR-5PC49170BY305693J'] s |
| 019 | rest | 422 | PASS | refund fresh on unpaid [422] issue=CANNOT_PROCESS_REFUNDS (expect 4xx: unpaid wires have no refundable money) |
| 020 | rest | 422,422 | OBSERVE | refund same-header [422, 422] ids_equal=True ids=['INV2-6WMV-8MJG-BUB3-SU79', 'INV2-6WMV-8MJG-BUB3-SU79'] sent |
| 021 | rest | 422,422 | OBSERVE | refund no-header [422, 422] distinct_refund_ids=1 ids=['INV2-HKYN-E54J-BJ5U-STLD', 'INV2-HKYN-E54J-BJ5U-STLD'] |
| 022 | rest | 422 | PASS | refund fresh on unpaid [422] issue=CANNOT_PROCESS_REFUNDS (expect 4xx: unpaid wires have no refundable money) |
| 023 | rest | 422,422 | OBSERVE | refund same-header [422, 422] ids_equal=True ids=['INV2-KH5U-LEUH-PFX8-ZTUU', 'INV2-KH5U-LEUH-PFX8-ZTUU'] sent |
| 024 | rest | 422,422 | OBSERVE | refund no-header [422, 422] distinct_refund_ids=1 ids=['INV2-U6P5-BXJU-ERNL-96MX', 'INV2-U6P5-BXJU-ERNL-96MX'] |
| 025 | rest | 200 | PASS | refund fresh on paid [200] |
| 026 | rest | 200,200 | OBSERVE | refund same-header [200, 200] ids_equal=False ids=['EXTR-1H295267XN648274U', 'EXTR-3S540392DD3965806'] sent=[' |
| 027 | rest | 200,200 | OBSERVE | refund no-header [200, 200] distinct_refund_ids=2 ids=['EXTR-9XF31922L5424403W', 'EXTR-0V054649FX730533F'] sen |
| 028 | rest | 201 | OBSERVE | forging observe [201] |
| 028 | mcp-stdio | 200 | PASS | mcp create ids=['INV2-49LY-76C4-QC6G-JM42'] ok=True |
| 031 | rest | 201 | OBSERVE | forging observe [201] |
| 031 | mcp-stdio | 200 | PASS | mcp create ids=['INV2-KCEB-FFSG-Q3RZ-FPL5'] ok=True |
| 034 | rest | 201 | OBSERVE | forging observe [201] |
| 034 | mcp-stdio | 200 | PASS | mcp create ids=['INV2-M3TP-5FWN-BC4R-99A7'] ok=True |
| 037 | rest | 200 | PASS | pay on DRAFT money=[200] (allowed-by-design) |
| 040 | rest | 200 | PASS | pay on AUTHORIZED_UNCAPTURED money=[200] (allowed-by-design) |
| 043 | rest | 422 | PASS | pay over remaining amount [422] issue=PAYMENT_AMOUNT_GREATER_THAN_AMOUNT_DUE |
| 046 | rest | 422 | PASS | refund on unpaid DRAFT invoice [422] issue=CANNOT_PROCESS_REFUNDS |
| 049 | rest | 422 | PASS | refund on unpaid AUTHORIZED_UNCAPTURED invoice [422] issue=CANNOT_PROCESS_REFUNDS |
| 052 | rest | 200 | PASS | refund within paid [200] |
| 055 | rest | 201,201,201 | OBSERVE | cumulative boundary profile x-x-x |
| 055 | mcp-stdio | 200 | PASS | mcp create ids=['INV2-HHRN-KPTG-BXUX-FH3L'] ok=True |
| 058 | rest | 201,201,201 | OBSERVE | cumulative boundary profile x-x-x |
| 058 | mcp-stdio | 200 | PASS | mcp create ids=['INV2-H89K-56FV-MV5L-2NHS'] ok=True |
| 061 | rest | 201,201,201 | OBSERVE | cumulative boundary profile x-x-x |
| 061 | mcp-stdio | 200 | PASS | mcp create ids=['INV2-UNVB-H2RC-4MG7-NNVY'] ok=True |
| 064 | rest | 200,200,200 | OBSERVE | cumulative boundary profile x-x-x |
| 067 | rest | 200,200,200 | OBSERVE | cumulative boundary profile x-x-x |
| 070 | rest | 200,200,200 | OBSERVE | cumulative boundary profile x-x-x |
| 073 | rest | 422,422,422 | OBSERVE | cumulative boundary profile 422-422-422 |
| 076 | rest | 422,422,422 | OBSERVE | cumulative boundary profile 422-422-422 |
| 079 | rest | 200,200,422 | OBSERVE | cumulative boundary profile x-x-422 |
| 082 | rest | 403 | DRIFT | echo-in-create [403] echo=no-invoice-id |
| 082 | mcp-stdio | 200 | DRIFT | mcp MASKED-FAILURE: isError=false but text ok:false (texts sample: {"ok":false,"status":406,"code":"PAYPAL_API |
| 085 | rest | 201 | DRIFT | echo-in-create [201] echo=reflected-verbatim |
| 085 | mcp-stdio | 200 | DRIFT | mcp create ids=['INV2-3EU4-CZMG-ZY7J-SND4'] ok=True echo=reflected-verbatim |
| 088 | rest | 403 | DRIFT | echo-in-create [403] echo=no-invoice-id |
| 088 | mcp-stdio | 200 | DRIFT | mcp MASKED-FAILURE: isError=false but text ok:false (texts sample: {"ok":false,"status":406,"code":"PAYPAL_API |
| 091 | rest | 200 | PASS | echo-in-payment-note [200] |
| 094 | rest | 403 | DRIFT | echo-in-payment-note [403] |
| 097 | rest | 200 | PASS | echo-in-payment-note [200] |
