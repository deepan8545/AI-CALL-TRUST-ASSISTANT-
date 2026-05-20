# Synthetic Data

All data in this directory is 100% synthetic. No real personal data, phone numbers, or audio is used.

## call_events.csv (12,000 rows)

| Column | Type | Description |
|---|---|---|
| row_id | int | Unique row identifier |
| phone_number_hash | str | SHA-256 hash of synthetic phone number |
| area_code | str | 3-digit area code |
| carrier_id | str | Carrier identifier |
| user_region | str | US state code |
| timestamp | str | ISO 8601 timestamp |
| call_duration_seconds | int | Duration (0 if not answered) |
| answered | int | 1 if answered, 0 if not |
| call_frequency_24h | int | Calls from this number in last 24h |
| call_frequency_7d | int | Calls from this number in last 7d |
| spoofing_signal | int | 1 if spoofing detected |
| complaint_count_7d | int | Complaints in last 7 days |
| complaint_count_30d | int | Complaints in last 30 days |
| known_business | int | 1 if number belongs to known business |
| business_verified | int | 1 if business is verified |
| known_scam_cluster | int | 1 if part of known scam cluster |
| blocklist_match | int | 1 if on blocklist |
| allowlist_match | int | 1 if on allowlist |
| first_seen_days_ago | int | Days since first seen |
| risk_score | float | Computed risk score (0-1) |
| risk_label | str | Safe / Unknown / Suspicious / High Risk |
| high_risk_binary | int | 1 if Suspicious or High Risk |

### Label Distribution
- Safe: ~55%
- Unknown: ~20%
- Suspicious: ~15%
- High Risk: ~10%

## scam_transcripts.csv (27 rows)

Labeled scam and safe transcript examples across 10 categories.

| Column | Type | Description |
|---|---|---|
| transcript_id | int | Unique ID |
| transcript | str | Call transcript text |
| category | str | Scam category or "safe" |
| is_scam | int | 1 if scam, 0 if safe |
| risk_score | float | Simulated risk score |
