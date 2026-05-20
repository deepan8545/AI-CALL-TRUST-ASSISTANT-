"""
Synthetic Call Event Data Generator
Generates 10,000+ rows with realistic distributions.
No real personal data — all hashed/synthetic identifiers.

Usage:
    python generate_synthetic_data.py
    # Outputs: data/synthetic/call_events.csv
    #          data/synthetic/scam_transcripts.csv
"""

import csv
import hashlib
import random
import os
from datetime import datetime, timedelta

random.seed(42)

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "synthetic")

# --- Config ---
NUM_ROWS = 12000
CARRIERS = ["carrier_att", "carrier_verizon", "carrier_tmobile", "carrier_sprint", "carrier_unknown", "carrier_voip_001", "carrier_voip_002"]
REGIONS = ["US-IL", "US-NY", "US-CA", "US-TX", "US-FL", "US-OH", "US-GA", "US-PA", "US-NC", "US-MI"]
AREA_CODES = ["212", "312", "415", "713", "305", "614", "404", "215", "704", "313", "800", "888", "900", "876"]

# Label distribution (realistic: most calls are safe)
LABEL_WEIGHTS = {
    "Safe": 0.55,
    "Unknown": 0.20,
    "Suspicious": 0.15,
    "High Risk": 0.10,
}

SCAM_CATEGORIES = [
    "bank_impersonation", "government_impersonation", "gift_card_scam",
    "tech_support_scam", "package_delivery_scam", "account_closure_threat",
    "healthcare_billing_scam", "credential_theft", "investment_scam", "insurance_scam",
]

SCAM_TRANSCRIPTS = {
    "bank_impersonation": [
        "This is your bank's fraud department. We detected unauthorized transactions on your account. Please verify your account number and PIN to secure your account immediately.",
        "Hello, this is the security team at your bank. Your debit card has been compromised. We need your card number and CVV to issue a replacement.",
        "Urgent notice from your bank. Your account will be frozen unless you confirm your identity. Please provide your social security number now.",
    ],
    "government_impersonation": [
        "This is the IRS. You owe back taxes and a warrant has been issued for your arrest. Pay immediately using gift cards to avoid prosecution.",
        "This is Social Security Administration. Your social security number has been suspended due to suspicious activity. Press 1 to speak with an officer.",
        "This is the Department of Treasury. You have an outstanding tax liability. Failure to pay today will result in legal action.",
    ],
    "gift_card_scam": [
        "You've won a prize! To claim your reward, purchase gift cards worth $500 and read the numbers to our verification department.",
        "This is customer support. To process your refund, we need you to purchase Google Play gift cards and share the codes.",
    ],
    "tech_support_scam": [
        "Your computer has been infected with a virus. We are Microsoft certified technicians. Give us remote access to fix the problem immediately.",
        "We detected malware on your device. Please download our remote access tool so we can remove the threat before your data is stolen.",
    ],
    "package_delivery_scam": [
        "Your package could not be delivered due to an incorrect address. Click the link to update your address and pay a small redelivery fee.",
        "UPS notice: your package is being held. Provide your credit card for the customs fee to release it.",
    ],
    "account_closure_threat": [
        "Your account will be permanently closed in 24 hours unless you verify your identity now. Press 1 to connect to our verification team.",
        "Final notice: your account has been flagged for closure. Provide your login credentials immediately to prevent permanent deletion.",
    ],
    "healthcare_billing_scam": [
        "You have an outstanding medical bill of $2,340. Provide your insurance information now or we will send this to collections today.",
        "This is the hospital billing department. Your insurance claim was denied. We need your policy number and social security to resubmit.",
    ],
    "credential_theft": [
        "We detected suspicious login activity on your account. Please provide your current password so we can secure your account.",
        "Your email has been compromised. Send us your password and we will reset your security settings immediately.",
    ],
    "investment_scam": [
        "Exclusive opportunity: invest $1000 today and earn guaranteed returns of 500% within 30 days. Wire transfer only. Limited spots available.",
        "Congratulations, you've been selected for a private investment program. Send your bank details to get started with zero risk.",
    ],
    "insurance_scam": [
        "Your car warranty is about to expire. Press 1 now to renew at a special discounted rate before it's too late.",
        "This is your insurance provider. Your policy has been cancelled due to non-payment. Provide your credit card to reinstate immediately.",
    ],
}

SAFE_TRANSCRIPTS = [
    "Hi, this is Dr. Smith's office calling to confirm your appointment tomorrow at 2pm. Please call us back to confirm.",
    "This is CVS Pharmacy. Your prescription is ready for pickup at the store on Main Street.",
    "Hello, this is United Airlines. Your flight UA 452 has been rescheduled to 3:15pm. No action needed.",
    "This is your dentist office reminding you of your cleaning appointment next Tuesday.",
    "Hi, this is the school office. Just confirming that your child was picked up at 3pm today.",
]


def generate_phone_hash():
    num = f"+1{random.choice(AREA_CODES)}{random.randint(1000000, 9999999)}"
    return hashlib.sha256(num.encode()).hexdigest()[:16]


def generate_row(row_id: int) -> dict:
    label = random.choices(
        list(LABEL_WEIGHTS.keys()),
        weights=list(LABEL_WEIGHTS.values()),
        k=1
    )[0]

    # Base features vary by label
    if label == "Safe":
        freq_24h = random.randint(0, 5)
        freq_7d = random.randint(0, 20)
        complaint_7d = 0
        complaint_30d = random.randint(0, 2)
        spoofing = False
        known_business = random.random() < 0.7
        business_verified = known_business and random.random() < 0.8
        known_scam_cluster = False
        blocklist = False
        allowlist = random.random() < 0.3
        first_seen = random.randint(60, 730)
        answered = random.random() < 0.85
        duration = random.randint(15, 600) if answered else 0
        carrier = random.choice(CARRIERS[:4])

    elif label == "Unknown":
        freq_24h = random.randint(3, 15)
        freq_7d = random.randint(10, 80)
        complaint_7d = random.randint(0, 3)
        complaint_30d = random.randint(0, 10)
        spoofing = random.random() < 0.1
        known_business = random.random() < 0.2
        business_verified = False
        known_scam_cluster = False
        blocklist = False
        allowlist = False
        first_seen = random.randint(7, 180)
        answered = random.random() < 0.5
        duration = random.randint(5, 120) if answered else 0
        carrier = random.choice(CARRIERS)

    elif label == "Suspicious":
        freq_24h = random.randint(10, 40)
        freq_7d = random.randint(50, 200)
        complaint_7d = random.randint(3, 15)
        complaint_30d = random.randint(10, 40)
        spoofing = random.random() < 0.4
        known_business = random.random() < 0.1
        business_verified = False
        known_scam_cluster = random.random() < 0.3
        blocklist = False
        allowlist = False
        first_seen = random.randint(3, 30)
        answered = random.random() < 0.3
        duration = random.randint(5, 60) if answered else 0
        carrier = random.choice(CARRIERS[3:])

    else:  # High Risk
        freq_24h = random.randint(25, 100)
        freq_7d = random.randint(150, 500)
        complaint_7d = random.randint(15, 60)
        complaint_30d = random.randint(40, 150)
        spoofing = random.random() < 0.75
        known_business = False
        business_verified = False
        known_scam_cluster = random.random() < 0.7
        blocklist = random.random() < 0.3
        allowlist = False
        first_seen = random.randint(0, 10)
        answered = random.random() < 0.15
        duration = random.randint(5, 45) if answered else 0
        carrier = random.choice(CARRIERS[4:])

    # Generate risk score from features (simulate what the scorer would produce)
    score = 0.30
    if business_verified: score -= 0.30
    elif known_business: score -= 0.15
    else: score += 0.05
    if complaint_7d >= 20: score += 0.30
    elif complaint_7d >= 10: score += 0.20
    elif complaint_7d >= 3: score += 0.10
    if complaint_30d >= 50: score += 0.10
    if known_scam_cluster: score += 0.25
    if spoofing: score += 0.20
    if freq_24h >= 50: score += 0.20
    elif freq_24h >= 20: score += 0.10
    if freq_7d >= 300: score += 0.10
    if first_seen <= 3: score += 0.10
    elif first_seen <= 7: score += 0.05
    if blocklist: score = 0.98
    if allowlist: score = 0.02
    score = max(0.0, min(1.0, round(score, 3)))

    high_risk_binary = 1 if label in ["Suspicious", "High Risk"] else 0

    timestamp = datetime(2026, 5, 1) + timedelta(
        days=random.randint(0, 18),
        hours=random.randint(6, 22),
        minutes=random.randint(0, 59),
    )

    return {
        "row_id": row_id,
        "phone_number_hash": generate_phone_hash(),
        "area_code": random.choice(AREA_CODES),
        "carrier_id": carrier,
        "user_region": random.choice(REGIONS),
        "timestamp": timestamp.isoformat(),
        "call_duration_seconds": duration,
        "answered": int(answered),
        "call_frequency_24h": freq_24h,
        "call_frequency_7d": freq_7d,
        "spoofing_signal": int(spoofing),
        "complaint_count_7d": complaint_7d,
        "complaint_count_30d": complaint_30d,
        "known_business": int(known_business),
        "business_verified": int(business_verified),
        "known_scam_cluster": int(known_scam_cluster),
        "blocklist_match": int(blocklist),
        "allowlist_match": int(allowlist),
        "first_seen_days_ago": first_seen,
        "risk_score": score,
        "risk_label": label,
        "high_risk_binary": high_risk_binary,
    }


def generate_transcript_dataset():
    """Generate labeled scam transcript dataset."""
    rows = []
    tid = 0
    # Scam transcripts
    for category, transcripts in SCAM_TRANSCRIPTS.items():
        for text in transcripts:
            tid += 1
            rows.append({
                "transcript_id": tid,
                "transcript": text,
                "category": category,
                "is_scam": 1,
                "risk_score": round(random.uniform(0.75, 0.98), 3),
            })
    # Safe transcripts
    for text in SAFE_TRANSCRIPTS:
        tid += 1
        rows.append({
            "transcript_id": tid,
            "transcript": text,
            "category": "safe",
            "is_scam": 0,
            "risk_score": round(random.uniform(0.01, 0.10), 3),
        })
    return rows


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # --- Call events ---
    call_events_path = os.path.join(OUTPUT_DIR, "call_events.csv")
    fieldnames = [
        "row_id", "phone_number_hash", "area_code", "carrier_id", "user_region",
        "timestamp", "call_duration_seconds", "answered",
        "call_frequency_24h", "call_frequency_7d", "spoofing_signal",
        "complaint_count_7d", "complaint_count_30d",
        "known_business", "business_verified", "known_scam_cluster",
        "blocklist_match", "allowlist_match", "first_seen_days_ago",
        "risk_score", "risk_label", "high_risk_binary",
    ]

    with open(call_events_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for i in range(NUM_ROWS):
            writer.writerow(generate_row(i + 1))

    # Count label distribution
    label_counts = {"Safe": 0, "Unknown": 0, "Suspicious": 0, "High Risk": 0}
    with open(call_events_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            label_counts[row["risk_label"]] += 1

    print(f"Generated {NUM_ROWS} call events → {call_events_path}")
    print(f"Label distribution: {label_counts}")

    # --- Transcripts ---
    transcripts = generate_transcript_dataset()
    transcripts_path = os.path.join(OUTPUT_DIR, "scam_transcripts.csv")
    t_fields = ["transcript_id", "transcript", "category", "is_scam", "risk_score"]

    with open(transcripts_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=t_fields)
        writer.writeheader()
        for row in transcripts:
            writer.writerow(row)

    print(f"Generated {len(transcripts)} transcripts → {transcripts_path}")


if __name__ == "__main__":
    main()
