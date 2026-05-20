# Data Strategy

## Privacy Rule

Do NOT collect real customer audio, transcripts, phone numbers, or personal data without consent, legal review, access controls, retention policy, and privacy approval.

For the MVP, use safe data only.

## Data Sources

### Public Complaint Data
- FCC unwanted call complaint data
- FTC Do Not Call reported calls data
- Hash or synthesize identifiers — never expose raw phone numbers in demos
- Aggregate by category, region, and time

### Synthetic Call Metadata
- 10,000+ generated rows with realistic distributions
- Fields: phone_number_hash, area_code, carrier_id, call frequencies, spoofing_signal, risk_label
- No privacy risk, fast iteration, good for architecture demos

### Public Voice Datasets
- Mozilla Common Voice for speech/audio pipeline testing
- ASVspoof-style datasets for synthetic voice research
- Do NOT promise production deepfake detection in 4 weeks

### Scam Transcript Examples
- Public consumer protection scam descriptions
- Manually written examples
- Synthetic transcripts from known scam patterns
- Categories: bank impersonation, government impersonation, gift card, tech support, account closure threat, verification code request, payment pressure, package delivery, healthcare billing, insurance

## Feature Engineering

### Metadata Features
call_frequency_1h, call_frequency_24h, call_frequency_7d, unique_users_called_24h, average_call_duration, answer_rate, complaint_count_7d, complaint_count_30d, first_seen_days_ago, area_code_mismatch, carrier_mismatch, spoofing_signal

### Reputation Features
known_business_identity, business_verified, previous_spam_reports, previous_safe_interactions, number_age, campaign_cluster_id, blocklist_match, allowlist_match

### Graph Features (from Neo4j)
connected_suspicious_numbers, shared_campaign_patterns, shared_target_users, similar_call_timing, community_risk_score, centrality_score, pagerank_score, node_similarity_score

### Voice/Transcript Features
urgent_language_detected, payment_request_detected, credential_request_detected, verification_code_request_detected, brand_impersonation_detected, synthetic_voice_score, transcript_similarity_to_known_scam
