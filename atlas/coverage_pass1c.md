# Coverage pass1c (2026-11-07)

counts: {"total_cells": 108, "scheduled_rest": 39, "executed_rest": 37, "scheduled_mcp": 12, "executed_mcp": 12, "not_scheduled": {"single-shape-pass-v0 (non-DUPLICATE abuse, FRESH only)": 54, "echo-refund: refund body has no text field on REST": 3, "mcp-shape-merge: one aggregate retry per cluster": 6, "mcp-tool-absent: SF-8 (record/refund not exposed by MCP)": 33}, "verdicts": {"PASS": 25, "DRIFT": 7, "OBSERVE": 19}}

## Not-scheduled reasons

- `  3` cells — echo-refund: refund body has no text field on REST (e.g. [100, 103, 106])
- `  6` cells — mcp-shape-merge: one aggregate retry per cluster (e.g. [2, 3, 5, 6, 8])
- ` 33` cells — mcp-tool-absent: SF-8 (record/refund not exposed by MCP) (e.g. [10, 11, 12, 13, 14])
- ` 54` cells — single-shape-pass-v0 (non-DUPLICATE abuse, FRESH only) (e.g. [29, 30, 32, 33, 35])

## Executed rows

| cell | transport | status chain | verdict | note |
|---|---|---|---|---|
| 001 | mcp-stdio | 200 | PASS | mcp create ids=['INV2-77K2-5E7Z-E6FQ-EHVH'] ok=True |
| 002 | rest | 201,201 | DRIFT | same-header pair ids DIVERGED [201, 201] sent=['bccc1702', 'bccc1702'] echoed=[None, None] |
| 003 | rest | 201,201 | PASS | no-header pair ids duplicated (documented hazard) [201, 201] sent=[None, None] echoed=[None, None] |
| 004 | mcp-stdio | 200 | PASS | mcp create ids=['INV2-YFAA-HN5V-VTE6-ZJJV'] ok=True |
| 005 | rest | 201,201 | DRIFT | same-header pair ids DIVERGED [201, 201] sent=['cf244392', 'cf244392'] echoed=[None, None] |
| 006 | rest | 201,201 | PASS | no-header pair ids duplicated (documented hazard) [201, 201] sent=[None, None] echoed=[None, None] |
| 007 | mcp-stdio | 200 | PASS | mcp create ids=['INV2-JG28-GVPB-H5MX-U2LH'] ok=True |
| 008 | rest | 201,201 | DRIFT | same-header pair ids DIVERGED [201, 201] sent=['ec4cacff', 'ec4cacff'] echoed=[None, None] |
| 009 | rest | 201,201 | PASS | no-header pair ids duplicated (documented hazard) [201, 201] sent=[None, None] echoed=[None, None] |
| 010 | rest | 200 | PASS | payment fresh [200] |
| 011 | rest | 200,200 | OBSERVE | payment same-header [200, 200] ids_equal=False ids=['EXTR-5DH758764W2268031', 'EXTR-30L450834X694152V'] sent=[ |
| 012 | rest | 200,200 | OBSERVE | payment no-header [200, 200] two_money_effects=True ids=['EXTR-54F0284489035192E', 'EXTR-6G030354JY454962H'] s |
| 013 | rest | 200 | PASS | payment fresh [200] |
| 014 | rest | 200,200 | OBSERVE | payment same-header [200, 200] ids_equal=False ids=['EXTR-36U363707B8691315', 'EXTR-7HC70005YG531815R'] sent=[ |
| 015 | rest | 200,200 | OBSERVE | payment no-header [200, 200] two_money_effects=True ids=['EXTR-6Y708954KK447511X', 'EXTR-46L11492EE9882200'] s |
| 018 | rest | 200,200 | OBSERVE | payment no-header [200, 200] two_money_effects=True ids=['EXTR-3HE40794Y1338023L', 'EXTR-7HF00483640526153'] s |
| 019 | rest | 422 | PASS | refund fresh on unpaid [422] issue=CANNOT_PROCESS_REFUNDS (expect 4xx: unpaid wires have no refundable money) |
| 020 | rest | 422,422 | OBSERVE | refund same-header [422, 422] ids_equal=True ids=['INV2-L4V7-KN72-Z3MX-CQKM', 'INV2-L4V7-KN72-Z3MX-CQKM'] sent |
| 021 | rest | 422,422 | OBSERVE | refund no-header [422, 422] distinct_refund_ids=1 ids=['INV2-QHZH-WAZK-EHBM-DQVL', 'INV2-QHZH-WAZK-EHBM-DQVL'] |
| 022 | rest | 422 | PASS | refund fresh on unpaid [422] issue=CANNOT_PROCESS_REFUNDS (expect 4xx: unpaid wires have no refundable money) |
| 023 | rest | 422,422 | OBSERVE | refund same-header [422, 422] ids_equal=True ids=['INV2-RA7V-EPBP-ERSB-QHHB', 'INV2-RA7V-EPBP-ERSB-QHHB'] sent |
| 024 | rest | 422,422 | OBSERVE | refund no-header [422, 422] distinct_refund_ids=1 ids=['INV2-HNY7-BKCH-5MPA-5AVB', 'INV2-HNY7-BKCH-5MPA-5AVB'] |
| 025 | rest | 200 | PASS | refund fresh on paid [200] |
| 026 | rest | 200,200 | OBSERVE | refund same-header [200, 200] ids_equal=False ids=['EXTR-8HJ86644AC714832L', 'EXTR-0Y324485FC075273F'] sent=[' |
| 027 | rest | 200,200 | OBSERVE | refund no-header [200, 200] distinct_refund_ids=2 ids=['EXTR-0LH06599DH658940J', 'EXTR-63Y91342M56507738'] sen |
| 028 | mcp-stdio | 200 | PASS | mcp create ids=['INV2-FFCD-5HC9-D2ML-NCRE'] ok=True |
| 031 | mcp-stdio | 200 | PASS | mcp create ids=['INV2-B6YG-375S-SHL9-ZZES'] ok=True |
| 034 | mcp-stdio | 200 | PASS | mcp create ids=['INV2-H8BU-9U4J-CBYQ-UM7H'] ok=True |
| 037 | rest | 200 | PASS | pay on DRAFT money=[200] (allowed-by-design) |
| 040 | rest | 200 | PASS | pay on AUTHORIZED_UNCAPTURED money=[200] (allowed-by-design) |
| 043 | rest | 422 | PASS | pay over remaining amount [422] issue=PAYMENT_AMOUNT_GREATER_THAN_AMOUNT_DUE |
| 046 | rest | 422 | PASS | refund on unpaid DRAFT invoice [422] issue=CANNOT_PROCESS_REFUNDS |
| 049 | rest | 422 | PASS | refund on unpaid AUTHORIZED_UNCAPTURED invoice [422] issue=CANNOT_PROCESS_REFUNDS |
| 052 | rest | 200 | PASS | refund within paid [200] |
| 055 | mcp-stdio | 200 | PASS | mcp create ids=['INV2-B2PR-SM3N-Z38T-AHWS'] ok=True |
| 058 | mcp-stdio | 200 | PASS | mcp create ids=['INV2-9UWG-JCUN-T9DF-DPLE'] ok=True |
| 061 | mcp-stdio | 200 | PASS | mcp create ids=['INV2-94SH-Z5Z7-AVNG-DCZV'] ok=True |
| 064 | rest | 200,200,200 | OBSERVE | cumulative boundary profile x-x-x |
| 067 | rest | 200,200,200 | OBSERVE | cumulative boundary profile x-x-x |
| 070 | rest | 200,200,200 | OBSERVE | cumulative boundary profile x-x-x |
| 073 | rest | 422,422,422 | OBSERVE | cumulative boundary profile 422-422-422 |
| 076 | rest | 422,422,422 | OBSERVE | cumulative boundary profile 422-422-422 |
| 079 | rest | 200,200,422 | OBSERVE | cumulative boundary profile x-x-422 |
| 082 | mcp-stdio | 200 | DRIFT | mcp MASKED-FAILURE: isError=false but text ok:false (texts sample: {"ok":false,"status":406,"code":"PAYPAL_API |
| 085 | mcp-stdio | 200 | DRIFT | mcp create ids=['INV2-6XRG-YRSD-5632-69HA'] ok=True echo=reflected-verbatim |
| 088 | mcp-stdio | 200 | DRIFT | mcp MASKED-FAILURE: isError=false but text ok:false (texts sample: {"ok":false,"status":406,"code":"PAYPAL_API |
| 091 | rest | 200 | PASS | echo-in-payment-note [200] |
| 094 | rest | 403 | DRIFT | echo-in-payment-note [403] |
| 097 | rest | 200 | PASS | echo-in-payment-note [200] |
