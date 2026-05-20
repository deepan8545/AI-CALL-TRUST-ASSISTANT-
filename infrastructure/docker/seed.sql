-- AI Call Trust Assistant — Seed Data
-- Demo-ready sample data for Day 3

-- =====================
-- Businesses
-- =====================
INSERT INTO businesses (id, name, verification_status, verified_phone_hashes, brand_display_name) VALUES
    ('a1b2c3d4-1111-4000-8000-000000000001', 'United Airlines', 'verified', ARRAY['hash_united_001', 'hash_united_002'], 'United Airlines'),
    ('a1b2c3d4-2222-4000-8000-000000000002', 'Chase Bank', 'verified', ARRAY['hash_chase_001'], 'Chase Bank'),
    ('a1b2c3d4-3333-4000-8000-000000000003', 'CVS Pharmacy', 'verified', ARRAY['hash_cvs_001'], 'CVS Pharmacy'),
    ('a1b2c3d4-4444-4000-8000-000000000004', 'Suspicious Corp', 'unverified', ARRAY['hash_sus_001'], 'Suspicious Corp'),
    ('a1b2c3d4-5555-4000-8000-000000000005', 'Legit Insurance Co', 'pending', ARRAY['hash_ins_001'], 'Legit Insurance');

-- =====================
-- Call Events
-- =====================
INSERT INTO call_events (id, phone_number_hash, carrier_id, timestamp, user_region, business_identity_id, call_duration_seconds, answered) VALUES
    -- Safe verified business call
    ('b1b2c3d4-0001-4000-8000-000000000001', 'hash_united_001', 'carrier_att', '2026-05-10T09:00:00Z', 'US-IL', 'a1b2c3d4-1111-4000-8000-000000000001', 45, true),
    -- Safe bank call
    ('b1b2c3d4-0002-4000-8000-000000000002', 'hash_chase_001', 'carrier_verizon', '2026-05-10T10:30:00Z', 'US-NY', 'a1b2c3d4-2222-4000-8000-000000000002', 120, true),
    -- Suspicious unknown caller
    ('b1b2c3d4-0003-4000-8000-000000000003', 'hash_scam_001', 'carrier_unknown', '2026-05-10T11:00:00Z', 'US-CA', NULL, 0, false),
    -- High-risk scam caller
    ('b1b2c3d4-0004-4000-8000-000000000004', 'hash_scam_002', 'carrier_unknown', '2026-05-10T11:30:00Z', 'US-TX', NULL, 30, true),
    -- Another scam from same cluster
    ('b1b2c3d4-0005-4000-8000-000000000005', 'hash_scam_003', 'carrier_unknown', '2026-05-10T12:00:00Z', 'US-FL', NULL, 15, true),
    -- Pharmacy reminder — safe
    ('b1b2c3d4-0006-4000-8000-000000000006', 'hash_cvs_001', 'carrier_tmobile', '2026-05-10T14:00:00Z', 'US-OH', 'a1b2c3d4-3333-4000-8000-000000000003', 60, true);

-- =====================
-- Risk Scores
-- =====================
INSERT INTO risk_scores (call_id, risk_score, risk_label, reason_codes, model_version) VALUES
    ('b1b2c3d4-0001-4000-8000-000000000001', 0.05, 'Safe', ARRAY['VERIFIED_BUSINESS', 'CLEAN_REPUTATION'], 'rules_v1'),
    ('b1b2c3d4-0002-4000-8000-000000000002', 0.08, 'Safe', ARRAY['VERIFIED_BUSINESS', 'KNOWN_BANK'], 'rules_v1'),
    ('b1b2c3d4-0003-4000-8000-000000000003', 0.62, 'Suspicious', ARRAY['UNKNOWN_CALLER', 'HIGH_FREQUENCY_24H', 'NO_BUSINESS_IDENTITY'], 'rules_v1'),
    ('b1b2c3d4-0004-4000-8000-000000000004', 0.91, 'High Risk', ARRAY['HIGH_COMPLAINT_VOLUME', 'SPOOFING_SIGNAL_DETECTED', 'SIMILAR_TO_SCAM_CLUSTER'], 'rules_v1'),
    ('b1b2c3d4-0005-4000-8000-000000000005', 0.87, 'High Risk', ARRAY['HIGH_COMPLAINT_VOLUME', 'PART_OF_KNOWN_CAMPAIGN', 'SPOOFING_SIGNAL_DETECTED'], 'rules_v1'),
    ('b1b2c3d4-0006-4000-8000-000000000006', 0.03, 'Safe', ARRAY['VERIFIED_BUSINESS', 'CLEAN_REPUTATION', 'PHARMACY_REMINDER'], 'rules_v1');

-- =====================
-- Scam Patterns
-- =====================
INSERT INTO scam_patterns (pattern_name, pattern_text, category) VALUES
    ('Bank Verification Code', 'This is your bank. Send the verification code now or your account will be closed.', 'bank_impersonation'),
    ('IRS Threat', 'This is the IRS. You owe back taxes and a warrant will be issued for your arrest.', 'government_impersonation'),
    ('Gift Card Payment', 'You need to pay with gift cards immediately to resolve this issue.', 'gift_card_scam'),
    ('Tech Support', 'Your computer has been compromised. Give me remote access to fix it now.', 'tech_support_scam'),
    ('Package Delivery', 'Your package could not be delivered. Click this link to update your address and pay a small fee.', 'package_delivery_scam'),
    ('Account Closure', 'Your account will be permanently closed in 24 hours unless you verify your identity now.', 'account_closure_threat'),
    ('Healthcare Billing', 'You have an outstanding medical bill. Provide your insurance information or face collections.', 'healthcare_billing_scam'),
    ('Password Reset', 'We detected suspicious activity. Please provide your current password to secure your account.', 'credential_theft');

-- =====================
-- Call Summaries (for demo calls)
-- =====================
INSERT INTO call_summaries (call_id, summary, action_items, sensitive_request_detected) VALUES
    ('b1b2c3d4-0001-4000-8000-000000000001', 'Verified United Airlines call regarding flight schedule change. No suspicious activity detected.', ARRAY['No action needed'], false),
    ('b1b2c3d4-0004-4000-8000-000000000004', 'Caller claimed to be from a bank and requested a verification code under pressure. Multiple scam signals detected.', ARRAY['Do not share the code', 'Contact the bank through the official app', 'Report the number'], true);
