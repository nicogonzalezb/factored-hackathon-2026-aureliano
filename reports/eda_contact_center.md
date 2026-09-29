# Contact-center demand analysis (first pass)

Silver layer, all history. Use this to pick and justify the workflow; re-run after full download.

## Contact reasons: volume, resolution, escalation

| reason_category | contact_reason | contacts | pct_volume | fcr_pct | escalated_pct | followup_pct | neg_sent_pct | median_handle_min | median_wait_min |
|---|---|---|---|---|---|---|---|---|---|
| Transaccional | Transaccional | 240,056 | 34.98 | 91.50 | 9.90 | 22.10 | 0.00 | 3.40 | 2.00 |
| Producto | Producto | 150,863 | 21.98 | 89.60 | 10.00 | 23.80 | 0.00 | 4.40 | 2.00 |
| Queja | Queja | 117,021 | 17.05 | 43.60 | 10.00 | 63.00 | 0.00 | 7.20 | 2.00 |
| Técnico | Técnico | 102,899 | 14.99 | 69.90 | 10.10 | 40.60 | 0.00 | 6.00 | 2.00 |
| Comercial | Comercial | 54,879 | 8.00 | 65.20 | 9.80 | 44.50 | 0.00 | 9.00 | 2.00 |
| Retención | Retención | 20,578 | 3.00 | 60.20 | 9.80 | 49.10 | 0.00 | 8.00 | 2.00 |

## Reason category by country

| country | reason_category | contacts | fcr_pct | escalated_pct |
|---|---|---|---|---|
| Argentina | Transaccional | 47,660 | 91.60 | 9.80 |
| Argentina | Producto | 29,948 | 89.60 | 10.00 |
| Argentina | Queja | 23,392 | 43.40 | 9.80 |
| Argentina | Técnico | 20,461 | 69.90 | 9.90 |
| Argentina | Comercial | 10,732 | 65.30 | 9.70 |
| Argentina | Retención | 4,124 | 59.70 | 10.90 |
| Colombia | Transaccional | 72,511 | 91.50 | 10.00 |
| Colombia | Producto | 45,564 | 89.80 | 10.10 |
| Colombia | Queja | 35,257 | 43.60 | 10.30 |
| Colombia | Técnico | 30,771 | 69.80 | 10.30 |
| Colombia | Comercial | 16,508 | 64.90 | 10.00 |
| Colombia | Retención | 6,179 | 60.70 | 9.00 |
| México | Transaccional | 119,885 | 91.50 | 9.90 |
| México | Producto | 75,351 | 89.60 | 9.90 |
| México | Queja | 58,372 | 43.70 | 10.00 |
| México | Técnico | 51,667 | 70.00 | 10.00 |
| México | Comercial | 27,639 | 65.40 | 9.80 |
| México | Retención | 10,275 | 60.00 | 9.90 |

## Channel mix

| channel | interaction_type | contacts | fcr_pct | median_wait_min |
|---|---|---|---|---|
| Phone | Inbound Call | 480,678 | 76.60 | 2.00 |
| Phone | Outbound Call | 102,572 | 76.60 |  |
| Email | Email | 27,543 | 76.80 |  |
| App | Chat | 22,947 | 77.00 |  |
| WhatsApp | Chat | 22,888 | 76.60 |  |
| Web Chat | Chat | 22,856 | 76.50 |  |
| App | Video | 3,417 | 77.80 |  |
| Web | Video | 3,395 | 76.70 |  |

## Monthly volume by reason category

| month | Comercial | Producto | Queja | Retención | Transaccional | Técnico |
|---|---|---|---|---|---|---|
| 2023-06 | 670 | 1,967 | 1,607 | 307 | 3,111 | 1,350 |
| 2023-07 | 1,510 | 4,232 | 3,296 | 581 | 6,703 | 2,939 |
| 2023-08 | 1,557 | 4,326 | 3,309 | 589 | 6,995 | 2,953 |
| 2023-09 | 1,517 | 4,017 | 3,222 | 540 | 6,341 | 2,712 |
| 2023-10 | 1,513 | 4,214 | 3,252 | 604 | 6,740 | 2,845 |
| 2023-11 | 1,488 | 4,042 | 3,173 | 596 | 6,652 | 2,783 |
| 2023-12 | 1,590 | 4,178 | 3,216 | 563 | 6,712 | 2,882 |
| 2024-01 | 1,528 | 4,165 | 3,223 | 563 | 6,675 | 2,793 |
| 2024-02 | 1,464 | 4,125 | 3,149 | 546 | 6,384 | 2,806 |
| 2024-03 | 1,537 | 4,131 | 3,221 | 585 | 6,720 | 2,758 |
| 2024-04 | 1,596 | 4,360 | 3,316 | 569 | 6,925 | 2,964 |
| 2024-05 | 1,592 | 4,183 | 3,230 | 597 | 6,667 | 2,886 |
| 2024-06 | 1,429 | 3,979 | 3,119 | 570 | 6,417 | 2,741 |
| 2024-07 | 1,571 | 4,304 | 3,362 | 569 | 6,830 | 2,940 |
| 2024-08 | 1,554 | 4,446 | 3,321 | 619 | 7,030 | 2,946 |
| 2024-09 | 1,493 | 4,202 | 3,296 | 545 | 6,579 | 2,725 |
| 2024-10 | 1,541 | 4,275 | 3,330 | 527 | 6,903 | 3,022 |
| 2024-11 | 1,361 | 3,911 | 2,957 | 518 | 6,238 | 2,706 |
| 2024-12 | 1,499 | 4,179 | 3,306 | 562 | 6,580 | 2,866 |
| 2025-01 | 1,498 | 4,304 | 3,359 | 546 | 6,831 | 2,975 |
| 2025-02 | 1,366 | 3,795 | 2,918 | 488 | 6,040 | 2,564 |
| 2025-03 | 1,558 | 4,283 | 3,353 | 549 | 6,884 | 2,896 |
| 2025-04 | 1,581 | 4,188 | 3,213 | 624 | 6,705 | 2,849 |
| 2025-05 | 1,557 | 4,351 | 3,348 | 629 | 6,891 | 2,969 |
| 2025-06 | 1,482 | 4,079 | 3,095 | 572 | 6,217 | 2,714 |
| 2025-07 | 1,601 | 4,300 | 3,437 | 619 | 6,739 | 3,020 |
| 2025-08 | 1,501 | 4,189 | 3,335 | 555 | 6,628 | 2,869 |
| 2025-09 | 1,565 | 4,161 | 3,318 | 612 | 6,787 | 2,874 |
| 2025-10 | 1,540 | 4,183 | 3,241 | 554 | 6,647 | 2,867 |
| 2025-11 | 1,535 | 4,155 | 3,248 | 596 | 6,595 | 2,878 |
| 2025-12 | 1,623 | 4,220 | 3,352 | 502 | 6,961 | 2,948 |
| 2026-01 | 1,512 | 4,242 | 3,259 | 576 | 6,470 | 2,772 |
| 2026-02 | 1,437 | 3,973 | 3,035 | 535 | 6,150 | 2,646 |
| 2026-03 | 1,602 | 4,489 | 3,432 | 610 | 7,172 | 3,101 |
| 2026-04 | 1,533 | 4,084 | 3,091 | 558 | 6,701 | 2,853 |
| 2026-05 | 1,498 | 4,162 | 3,112 | 554 | 6,621 | 2,827 |
| 2026-06 | 880 | 2,469 | 1,970 | 349 | 3,815 | 1,660 |

## CSAT / NPS by contact reason

| contact_reason | survey_type | surveys | avg_score | detractor_pct |
|---|---|---|---|---|
| Queja | CSAT | 21,843 | 2.43 | 0.00 |
| Queja | CES | 3,693 | 2.43 | 0.00 |
| Retención | CSAT | 3,798 | 2.61 | 0.00 |
| Retención | CES | 640 | 2.62 | 0.00 |
| Comercial | CSAT | 10,243 | 2.66 | 0.00 |
| Comercial | CES | 1,760 | 2.67 | 0.00 |
| Técnico | CSAT | 19,193 | 2.70 | 0.00 |
| Técnico | CES | 3,161 | 2.70 | 0.00 |
| Producto | CSAT | 27,942 | 2.90 | 0.00 |
| Producto | CES | 4,627 | 2.91 | 0.00 |
| Transaccional | CSAT | 44,837 | 2.91 | 0.00 |
| Transaccional | CES | 7,354 | 2.91 | 0.00 |
| Queja | NPS | 10,821 | 4.33 | 80.80 |
| Retención | NPS | 1,917 | 4.77 | 77.40 |
| Comercial | NPS | 5,144 | 4.95 | 74.00 |
| Técnico | NPS | 9,448 | 5.14 | 72.40 |
| Producto | NPS | 13,997 | 5.69 | 66.70 |
| Transaccional | NPS | 22,341 | 5.74 | 66.20 |

## Complaints (PQR): category, SLA, resolution

| case_type | category | cases | sla_breached_pct | median_resolution_days | escalated_pct | repeat_pct |
|---|---|---|---|---|---|---|
| Complaint | Transactions | 8,239 | 20.00 | 16.00 | 5.00 | 14.80 |
| Complaint | Fees | 8,171 | 20.10 | 16.00 | 5.10 | 15.50 |
| Complaint | Technical | 8,120 | 20.00 | 16.00 | 4.80 | 15.00 |
| Complaint | Branch | 7,969 | 20.40 | 16.00 | 4.50 | 15.30 |
| Complaint | Service | 7,953 | 19.90 | 16.00 | 5.20 | 14.70 |
| Claim | Fees | 3,357 | 19.10 | 16.00 | 5.70 | 15.40 |
| Claim | Branch | 3,355 | 19.90 | 16.00 | 4.60 | 15.10 |
| Claim | Transactions | 3,335 | 20.90 | 15.00 | 5.00 | 14.40 |
| Claim | Technical | 3,312 | 19.20 | 15.00 | 5.20 | 14.90 |
| Claim | Service | 3,239 | 20.60 | 16.00 | 5.30 | 15.50 |
| Request | Branch | 1,372 | 20.00 | 15.00 | 4.70 | 15.20 |
| Request | Fees | 1,367 | 20.40 | 15.00 | 4.40 | 13.90 |
| Request | Service | 1,358 | 21.20 | 16.00 | 4.90 | 14.50 |
| Request | Technical | 1,335 | 20.40 | 16.00 | 4.10 | 15.60 |
| Request | Transactions | 1,329 | 19.20 | 15.00 | 4.70 | 14.30 |
| Suggestion | Transactions | 677 | 20.20 | 16.00 | 5.60 | 15.10 |
| Suggestion | Branch | 665 | 23.60 | 15.00 | 3.60 | 13.20 |
| Suggestion | Fees | 658 | 18.50 | 15.50 | 5.30 | 13.80 |
| Suggestion | Service | 644 | 20.70 | 18.00 | 5.40 | 14.90 |
| Suggestion | Technical | 640 | 23.60 | 15.00 | 6.10 | 19.50 |

## Transcript language / accent coverage

| detected_language | detected_accent | transcripts | avg_accent_conf | pct |
|---|---|---|---|---|
| es |  | 63,083 | 1.00 | 36.82 |
| es | mexican | 54,152 | 1.00 | 31.61 |
| es | colombian | 32,284 | 1.00 | 18.84 |
| es | argentine | 21,802 | 1.00 | 12.73 |

## Most frequent transcript intents

| intent | n |
|---|---|
| consulta_general | 162,864 |

## Transaction status / disputes signal

| transaction_type | transaction_status | txns | fraud_pct |
|---|---|---|---|
| Purchase | Approved | 996,168 | 0.10 |
| Withdrawal | Approved | 887,765 | 0.10 |
| Transfer | Approved | 824,676 | 0.09 |
| Payment | Approved | 679,954 | 0.10 |
| Deposit | Approved | 560,724 | 0.10 |
| Adjustment | Approved | 121,394 | 0.11 |
| Purchase | Declined | 54,565 | 0.10 |
| Withdrawal | Declined | 47,911 | 0.09 |
| Transfer | Declined | 44,979 | 0.09 |
| Payment | Declined | 36,851 | 0.09 |
| Deposit | Declined | 30,240 | 0.13 |
| Purchase | Pending | 21,595 | 0.09 |
| Withdrawal | Pending | 19,247 | 0.08 |
| Transfer | Pending | 17,841 | 0.08 |
| Payment | Pending | 14,684 | 0.08 |
| Deposit | Pending | 12,268 | 0.10 |
| Purchase | Reversed | 11,078 | 0.04 |
| Withdrawal | Reversed | 9,750 | 0.09 |
| Transfer | Reversed | 8,942 | 0.08 |
| Payment | Reversed | 7,475 | 0.11 |
| Adjustment | Declined | 6,688 | 0.09 |
| Deposit | Reversed | 6,177 | 0.10 |
| Adjustment | Pending | 2,708 | 0.22 |
| Adjustment | Reversed | 1,328 | 0.07 |
