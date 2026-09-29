# Data quality report

Generated 2026-09-29 00:43 UTC from `data/silver`, contracts `contracts/tables.yml`.

| table | rows | errors | warnings | exact dups removed | pk conflicts | late >1d |
|---|---:|---:|---:|---:|---:|---:|
| branches | 350 | 0 | 1 | 0 | 0 |  |
| call_center_interactions | 686,296 | 0 | 5 | 0 | 0 | 0.0% |
| call_transcripts | 171,321 | 1 | 1 | 0 | 0 |  |
| campaign_sends | 1,746,801 | 0 | 2 | 0 | 0 | 0.0% |
| complaints | 67,095 | 0 | 2 | 0 | 0 | 0.0% |
| customers | 150,000 | 0 | 3 | 0 | 0 |  |
| daily_exchange_rates | 13,164 | 0 | 1 | 0 | 0 |  |
| digital_events | 15,620,994 | 0 | 2 | 0 | 0 | 0.0% |
| marketing_campaigns | 200 | 0 | 0 | 0 | 0 |  |
| products | 400,000 | 1 | 0 | 0 | 0 |  |
| satisfaction_surveys | 212,759 | 0 | 2 | 0 | 0 | 0.0% |
| service_agents | 1,200 | 1 | 1 | 0 | 0 |  |
| transactions | 4,425,008 | 0 | 2 | 0 | 0 | 0.0% |

## branches


| status | check | failed | total | % | detail |
|---|---|---:|---:|---:|---|
| warn | enum: geographic_zone | 350 | 350 | 100.0 | {"Urbana": 350} |

## call_center_interactions

Event range: 2023-06-17 08:03:26 → 2026-06-18 07:58:13  
Late arrival: `{"lag_days_p50": 0.0, "lag_days_p95": 0.0, "lag_days_max": 0, "rows_processed_>1_day_late": 0, "rows_processed_before_event": 228318}`  

| status | check | failed | total | % | detail |
|---|---|---:|---:|---:|---|
| warn | row count within 10% of documented | 1 | 1 | 100.0 | {"silver": 686296, "documented": 800000} |
| warn | enum: channel | 3,395 | 686,296 | 0.495 | {"Web": 3395} |
| warn | enum: reason_category | 686,296 | 686,296 | 100.0 | {"Transaccional": 240056, "Producto": 150863, "Queja": 117021, "Técnico": 102899, "Comercial": 54879, "Retención": 20578} |
| warn | enum: detected_sentiment | 226,584 | 686,296 | 33.015 | {"Negativo": 94322, "Positivo": 75562, "Muy Negativo": 37727, "Muy Positivo": 18973} |
| warn | process_date before event date | 228,318 | 686,296 | 33.268 |  |

Highest null %: `mentioned_products` 60.026%, `wait_time_seconds` 29.961%, `customer_detected_accent` 29.834%, `agent_used_accent` 29.834%, `duration_seconds` 14.022%

## call_transcripts


| status | check | failed | total | % | detail |
|---|---|---:|---:|---:|---|
| warn | row count within 10% of documented | 1 | 1 | 100.0 | {"silver": 171321, "documented": 200000} |
| fail | not null: duration_seconds | 24,029 | 171,321 | 14.026 |  |

Highest null %: `detected_accent` 36.822%, `duration_seconds` 14.026%, `mentioned_entities` 10.019%, `accent_confidence` 10.005%, `detected_keywords` 5.135%, `audio_quality` 5.042%, `detected_intents` 4.936%

## campaign_sends

Event range: 2023-07-01 06:00:42 → 2026-06-18 05:59:53  
Late arrival: `{"lag_days_p50": 0.0, "lag_days_p95": 0.0, "lag_days_max": 0, "rows_processed_>1_day_late": 0, "rows_processed_before_event": 436429}`  

| status | check | failed | total | % | detail |
|---|---|---:|---:|---:|---|
| warn | row count within 10% of documented | 1 | 1 | 100.0 | {"silver": 1746801, "documented": 2000000} |
| warn | process_date before event date | 436,429 | 1,746,801 | 24.984 |  |

Highest null %: `conversion_date` 99.439%, `conversion_value` 99.439%, `click_date` 94.402%, `click_count` 94.402%, `failure_reason` 94.298%, `open_device` 74.904%, `open_country` 74.896%, `open_date` 72.103%

## complaints

Event range: 2023-06-17 08:07:05 → 2026-06-18 07:56:52  
Late arrival: `{"lag_days_p50": 0.0, "lag_days_p95": 0.0, "lag_days_max": 0, "rows_processed_>1_day_late": 0, "rows_processed_before_event": 22585}`  

| status | check | failed | total | % | detail |
|---|---|---:|---:|---:|---|
| warn | row count within 10% of documented | 1 | 1 | 100.0 | {"silver": 67095, "documented": 80000} |
| warn | process_date before event date | 22,585 | 67,095 | 33.661 |  |

Highest null %: `origin_interaction_id` 100.0%, `closing_date` 96.302%, `resolution_satisfaction` 96.298%, `compensation_granted` 93.083%, `resolution` 77.182%, `resolution_date` 77.123%, `resolution_days` 77.103%, `related_branch_id` 71.417%

## customers


| status | check | failed | total | % | detail |
|---|---|---:|---:|---:|---|
| warn | enum: document_type | 15,062 | 150,000 | 10.041 | {"Pasaporte": 15062} |
| warn | enum: country | 74,907 | 150,000 | 49.938 | {"México": 74907} |
| warn | fk: registration_branch_id -> branches.branch_id | 149,995 | 150,000 | 99.997 |  |

Highest null %: `landline_phone` 50.035%, `detected_accent` 29.878%, `estimated_monthly_income` 20.022%, `credit_score` 14.995%, `education_level` 11.968%, `postal_code` 10.029%, `occupation` 10.026%, `marital_status` 7.97%

## daily_exchange_rates


| status | check | failed | total | % | detail |
|---|---|---:|---:|---:|---|
| warn | row count within 10% of documented | 1 | 1 | 100.0 | {"silver": 13164, "documented": 3000} |

## digital_events

Event range: 2023-06-17 06:02:03 → 2026-06-18 06:04:05  
Late arrival: `{"lag_days_p50": 0.0, "lag_days_p95": 0.0, "lag_days_max": 0, "rows_processed_>1_day_late": 0, "rows_processed_before_event": 3930816}`  

| status | check | failed | total | % | detail |
|---|---|---:|---:|---:|---|
| warn | row count within 10% of documented | 1 | 1 | 100.0 | {"silver": 15620994, "documented": 10000000} |
| warn | process_date before event date | 3,930,816 | 15,620,994 | 25.164 |  |

Highest null %: `event_value` 94.914%, `utm_campaign` 94.63%, `utm_source` 94.629%, `utm_medium` 94.628%, `referrer` 93.294%, `product_id` 90.779%, `duration_seconds` 63.672%, `browser` 62.017%

## marketing_campaigns

All checks pass.

Highest null %: `target_country` 55.5%, `target_segment` 39.5%, `description` 19.5%, `budget` 15.5%, `promoted_product` 11.0%, `expected_conversion_rate` 7.0%

## products


| status | check | failed | total | % | detail |
|---|---|---:|---:|---:|---|
| fail | unique: product_number | 6 | 400,000 | 0.002 |  |

Highest null %: `credit_limit` 68.671%, `days_past_due` 68.662%, `expiration_date` 66.71%, `last_transaction_date` 23.569%, `interest_rate` 10.017%

## satisfaction_surveys

Event range: 2023-06-17 09:29:20 → 2026-06-19 06:54:58  
Late arrival: `{"lag_days_p50": -1.0, "lag_days_p95": 0.0, "lag_days_max": 0, "rows_processed_>1_day_late": 0, "rows_processed_before_event": 169092}`  

| status | check | failed | total | % | detail |
|---|---|---:|---:|---:|---|
| warn | row count within 10% of documented | 1 | 1 | 100.0 | {"silver": 212759, "documented": 250000} |
| warn | process_date before event date | 169,092 | 212,759 | 79.476 |  |

Highest null %: `question_3_response` 81.151%, `question_3_text` 81.132%, `nps_category` 71.614%, `question_2_text` 61.754%, `question_2_response` 61.696%, `open_comments` 52.436%, `comment_sentiment` 52.408%, `question_1_text` 42.986%

## service_agents


| status | check | failed | total | % | detail |
|---|---|---:|---:|---:|---|
| fail | unique: employee_code | 13 | 1,200 | 1.083 |  |
| warn | fk: assigned_branch_id -> branches.branch_id | 831 | 833 | 99.76 |  |

Highest null %: `specialty` 39.667%, `assigned_branch_id` 30.583%, `avg_csat` 11.167%, `total_monthly_interactions` 9.25%, `phone` 5.75%

## transactions

Event range: 2023-06-17 06:01:30 → 2026-06-18 05:59:41  
Late arrival: `{"lag_days_p50": 0.0, "lag_days_p95": 0.0, "lag_days_max": 0, "rows_processed_>1_day_late": 0, "rows_processed_before_event": 1106307}`  

| status | check | failed | total | % | detail |
|---|---|---:|---:|---:|---|
| warn | row count within 10% of documented | 1 | 1 | 100.0 | {"silver": 4425008, "documented": 5000000} |
| warn | process_date before event date | 1,106,307 | 4,425,008 | 25.001 |  |

Highest null %: `longitude` 80.626%, `latitude` 80.625%, `merchant_category` 76.75%, `merchant_name` 76.741%, `branch_id` 68.634%, `transaction_category` 60.87%, `amount_usd` 57.344%, `fraud_score` 20.004%
