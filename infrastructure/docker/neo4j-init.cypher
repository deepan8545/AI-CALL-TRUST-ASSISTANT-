// =============================================
// AI Call Trust Assistant — Neo4j Graph Schema
// Day 6: Init script
// =============================================

// --- Constraints ---
CREATE CONSTRAINT phone_hash_unique IF NOT EXISTS FOR (p:PhoneNumber) REQUIRE p.phone_number_hash IS UNIQUE;
CREATE CONSTRAINT business_id_unique IF NOT EXISTS FOR (b:Business) REQUIRE b.business_id IS UNIQUE;
CREATE CONSTRAINT carrier_id_unique IF NOT EXISTS FOR (c:Carrier) REQUIRE c.carrier_id IS UNIQUE;
CREATE CONSTRAINT campaign_id_unique IF NOT EXISTS FOR (sc:ScamCampaign) REQUIRE sc.campaign_id IS UNIQUE;
CREATE CONSTRAINT region_code_unique IF NOT EXISTS FOR (r:Region) REQUIRE r.region_code IS UNIQUE;

// --- Indexes ---
CREATE INDEX phone_reputation IF NOT EXISTS FOR (p:PhoneNumber) ON (p.reputation_score);
CREATE INDEX complaint_date IF NOT EXISTS FOR (c:Complaint) ON (c.created_at);
CREATE INDEX campaign_active IF NOT EXISTS FOR (sc:ScamCampaign) ON (sc.active);

// =============================================
// SEED DATA — Sample Fraud Cluster
// =============================================

// --- Carriers ---
CREATE (att:Carrier {carrier_id: 'carrier_att', name: 'AT&T', risk_level: 'low'});
CREATE (vz:Carrier {carrier_id: 'carrier_verizon', name: 'Verizon', risk_level: 'low'});
CREATE (tm:Carrier {carrier_id: 'carrier_tmobile', name: 'T-Mobile', risk_level: 'low'});
CREATE (unk:Carrier {carrier_id: 'carrier_unknown', name: 'Unknown Carrier', risk_level: 'high'});

// --- Regions ---
CREATE (:Region {region_code: 'US-IL', name: 'Illinois'});
CREATE (:Region {region_code: 'US-NY', name: 'New York'});
CREATE (:Region {region_code: 'US-CA', name: 'California'});
CREATE (:Region {region_code: 'US-TX', name: 'Texas'});
CREATE (:Region {region_code: 'US-FL', name: 'Florida'});

// --- Verified Businesses ---
CREATE (united:Business {business_id: 'biz_united', name: 'United Airlines', verified: true});
CREATE (chase:Business {business_id: 'biz_chase', name: 'Chase Bank', verified: true});
CREATE (cvs:Business {business_id: 'biz_cvs', name: 'CVS Pharmacy', verified: true});

// --- Safe Phone Numbers (verified businesses) ---
CREATE (p_united:PhoneNumber {phone_number_hash: 'hash_united_001', reputation_score: 0.95, first_seen_days_ago: 730, complaint_count_7d: 0, complaint_count_30d: 0});
CREATE (p_chase:PhoneNumber {phone_number_hash: 'hash_chase_001', reputation_score: 0.92, first_seen_days_ago: 500, complaint_count_7d: 0, complaint_count_30d: 1});
CREATE (p_cvs:PhoneNumber {phone_number_hash: 'hash_cvs_001', reputation_score: 0.90, first_seen_days_ago: 400, complaint_count_7d: 0, complaint_count_30d: 0});

// Safe numbers → businesses
MATCH (p:PhoneNumber {phone_number_hash: 'hash_united_001'}), (b:Business {business_id: 'biz_united'})
CREATE (p)-[:BELONGS_TO]->(b);
MATCH (p:PhoneNumber {phone_number_hash: 'hash_chase_001'}), (b:Business {business_id: 'biz_chase'})
CREATE (p)-[:BELONGS_TO]->(b);
MATCH (p:PhoneNumber {phone_number_hash: 'hash_cvs_001'}), (b:Business {business_id: 'biz_cvs'})
CREATE (p)-[:BELONGS_TO]->(b);

// Safe numbers → carriers
MATCH (p:PhoneNumber {phone_number_hash: 'hash_united_001'}), (c:Carrier {carrier_id: 'carrier_att'})
CREATE (p)-[:USES_CARRIER]->(c);
MATCH (p:PhoneNumber {phone_number_hash: 'hash_chase_001'}), (c:Carrier {carrier_id: 'carrier_verizon'})
CREATE (p)-[:USES_CARRIER]->(c);
MATCH (p:PhoneNumber {phone_number_hash: 'hash_cvs_001'}), (c:Carrier {carrier_id: 'carrier_tmobile'})
CREATE (p)-[:USES_CARRIER]->(c);

// --- Scam Campaign: "Bank Verification Scam Ring" ---
CREATE (campaign1:ScamCampaign {campaign_id: 'campaign_bank_verify', name: 'Bank Verification Scam Ring', category: 'bank_impersonation', active: true, first_detected: '2026-04-15'});

// Scam phone numbers
CREATE (s1:PhoneNumber {phone_number_hash: 'hash_scam_001', reputation_score: 0.08, first_seen_days_ago: 5, complaint_count_7d: 22, complaint_count_30d: 45});
CREATE (s2:PhoneNumber {phone_number_hash: 'hash_scam_002', reputation_score: 0.05, first_seen_days_ago: 3, complaint_count_7d: 31, complaint_count_30d: 60});
CREATE (s3:PhoneNumber {phone_number_hash: 'hash_scam_003', reputation_score: 0.10, first_seen_days_ago: 7, complaint_count_7d: 18, complaint_count_30d: 35});
CREATE (s4:PhoneNumber {phone_number_hash: 'hash_scam_004', reputation_score: 0.06, first_seen_days_ago: 2, complaint_count_7d: 40, complaint_count_30d: 80});

// Scam numbers → unknown carrier
MATCH (s:PhoneNumber {phone_number_hash: 'hash_scam_001'}), (c:Carrier {carrier_id: 'carrier_unknown'}) CREATE (s)-[:USES_CARRIER]->(c);
MATCH (s:PhoneNumber {phone_number_hash: 'hash_scam_002'}), (c:Carrier {carrier_id: 'carrier_unknown'}) CREATE (s)-[:USES_CARRIER]->(c);
MATCH (s:PhoneNumber {phone_number_hash: 'hash_scam_003'}), (c:Carrier {carrier_id: 'carrier_unknown'}) CREATE (s)-[:USES_CARRIER]->(c);
MATCH (s:PhoneNumber {phone_number_hash: 'hash_scam_004'}), (c:Carrier {carrier_id: 'carrier_unknown'}) CREATE (s)-[:USES_CARRIER]->(c);

// Scam numbers → campaign
MATCH (s:PhoneNumber {phone_number_hash: 'hash_scam_001'}), (c:ScamCampaign {campaign_id: 'campaign_bank_verify'}) CREATE (s)-[:PART_OF_CAMPAIGN]->(c);
MATCH (s:PhoneNumber {phone_number_hash: 'hash_scam_002'}), (c:ScamCampaign {campaign_id: 'campaign_bank_verify'}) CREATE (s)-[:PART_OF_CAMPAIGN]->(c);
MATCH (s:PhoneNumber {phone_number_hash: 'hash_scam_003'}), (c:ScamCampaign {campaign_id: 'campaign_bank_verify'}) CREATE (s)-[:PART_OF_CAMPAIGN]->(c);
MATCH (s:PhoneNumber {phone_number_hash: 'hash_scam_004'}), (c:ScamCampaign {campaign_id: 'campaign_bank_verify'}) CREATE (s)-[:PART_OF_CAMPAIGN]->(c);

// Scam numbers — similar behavior links
MATCH (a:PhoneNumber {phone_number_hash: 'hash_scam_001'}), (b:PhoneNumber {phone_number_hash: 'hash_scam_002'}) CREATE (a)-[:SIMILAR_BEHAVIOR_TO {similarity: 0.91}]->(b);
MATCH (a:PhoneNumber {phone_number_hash: 'hash_scam_002'}), (b:PhoneNumber {phone_number_hash: 'hash_scam_003'}) CREATE (a)-[:SIMILAR_BEHAVIOR_TO {similarity: 0.85}]->(b);
MATCH (a:PhoneNumber {phone_number_hash: 'hash_scam_003'}), (b:PhoneNumber {phone_number_hash: 'hash_scam_004'}) CREATE (a)-[:SIMILAR_BEHAVIOR_TO {similarity: 0.88}]->(b);
MATCH (a:PhoneNumber {phone_number_hash: 'hash_scam_001'}), (b:PhoneNumber {phone_number_hash: 'hash_scam_004'}) CREATE (a)-[:SIMILAR_BEHAVIOR_TO {similarity: 0.79}]->(b);

// Campaign targets regions
MATCH (c:ScamCampaign {campaign_id: 'campaign_bank_verify'}), (r:Region {region_code: 'US-TX'}) CREATE (c)-[:TARGETS_REGION]->(r);
MATCH (c:ScamCampaign {campaign_id: 'campaign_bank_verify'}), (r:Region {region_code: 'US-FL'}) CREATE (c)-[:TARGETS_REGION]->(r);
MATCH (c:ScamCampaign {campaign_id: 'campaign_bank_verify'}), (r:Region {region_code: 'US-CA'}) CREATE (c)-[:TARGETS_REGION]->(r);

// --- Complaints ---
CREATE (comp1:Complaint {complaint_id: 'comp_001', category: 'bank_impersonation', created_at: '2026-05-08'});
CREATE (comp2:Complaint {complaint_id: 'comp_002', category: 'bank_impersonation', created_at: '2026-05-09'});
CREATE (comp3:Complaint {complaint_id: 'comp_003', category: 'verification_code_request', created_at: '2026-05-10'});

MATCH (s:PhoneNumber {phone_number_hash: 'hash_scam_001'}), (c:Complaint {complaint_id: 'comp_001'}) CREATE (s)-[:REPORTED_IN]->(c);
MATCH (s:PhoneNumber {phone_number_hash: 'hash_scam_002'}), (c:Complaint {complaint_id: 'comp_002'}) CREATE (s)-[:REPORTED_IN]->(c);
MATCH (s:PhoneNumber {phone_number_hash: 'hash_scam_002'}), (c:Complaint {complaint_id: 'comp_003'}) CREATE (s)-[:REPORTED_IN]->(c);

// --- Scam Patterns ---
CREATE (pat1:ScamPattern {pattern_id: 'pat_bank_verify', name: 'Bank Verification Code', category: 'bank_impersonation'});
CREATE (pat2:ScamPattern {pattern_id: 'pat_account_closure', name: 'Account Closure Threat', category: 'account_closure_threat'});

MATCH (s:PhoneNumber {phone_number_hash: 'hash_scam_001'}), (p:ScamPattern {pattern_id: 'pat_bank_verify'}) CREATE (s)-[:MATCHES_PATTERN]->(p);
MATCH (s:PhoneNumber {phone_number_hash: 'hash_scam_002'}), (p:ScamPattern {pattern_id: 'pat_bank_verify'}) CREATE (s)-[:MATCHES_PATTERN]->(p);
MATCH (s:PhoneNumber {phone_number_hash: 'hash_scam_004'}), (p:ScamPattern {pattern_id: 'pat_account_closure'}) CREATE (s)-[:MATCHES_PATTERN]->(p);

// --- Transcript Signals ---
CREATE (ts1:TranscriptSignal {signal_id: 'sig_verify_code', name: 'Verification Code Request', risk_weight: 0.8});
CREATE (ts2:TranscriptSignal {signal_id: 'sig_urgency', name: 'Urgent Pressure Language', risk_weight: 0.6});
CREATE (ts3:TranscriptSignal {signal_id: 'sig_brand_impersonation', name: 'Brand Impersonation', risk_weight: 0.7});

// --- Second Campaign: "IRS Threat Scam" ---
CREATE (campaign2:ScamCampaign {campaign_id: 'campaign_irs_threat', name: 'IRS Threat Scam', category: 'government_impersonation', active: true, first_detected: '2026-04-20'});
CREATE (irs1:PhoneNumber {phone_number_hash: 'hash_irs_001', reputation_score: 0.03, first_seen_days_ago: 4, complaint_count_7d: 55, complaint_count_30d: 120});
CREATE (irs2:PhoneNumber {phone_number_hash: 'hash_irs_002', reputation_score: 0.04, first_seen_days_ago: 6, complaint_count_7d: 38, complaint_count_30d: 90});

MATCH (s:PhoneNumber {phone_number_hash: 'hash_irs_001'}), (c:ScamCampaign {campaign_id: 'campaign_irs_threat'}) CREATE (s)-[:PART_OF_CAMPAIGN]->(c);
MATCH (s:PhoneNumber {phone_number_hash: 'hash_irs_002'}), (c:ScamCampaign {campaign_id: 'campaign_irs_threat'}) CREATE (s)-[:PART_OF_CAMPAIGN]->(c);
MATCH (a:PhoneNumber {phone_number_hash: 'hash_irs_001'}), (b:PhoneNumber {phone_number_hash: 'hash_irs_002'}) CREATE (a)-[:SIMILAR_BEHAVIOR_TO {similarity: 0.93}]->(b);
MATCH (c:ScamCampaign {campaign_id: 'campaign_irs_threat'}), (r:Region {region_code: 'US-IL'}) CREATE (c)-[:TARGETS_REGION]->(r);
MATCH (c:ScamCampaign {campaign_id: 'campaign_irs_threat'}), (r:Region {region_code: 'US-NY'}) CREATE (c)-[:TARGETS_REGION]->(r);
