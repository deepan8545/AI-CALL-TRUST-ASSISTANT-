# Feature Store Design

## Principle

Training features and serving features must come from the same pipeline. Feature skew between training and inference is the #1 cause of ML model degradation in production.

## Feature Groups

### 1. Metadata Features (real-time, from call event)
| Feature | Type | Source | Latency |
|---|---|---|---|
| call_frequency_24h | int | Call event metadata | <1ms |
| call_frequency_7d | int | Call event metadata | <1ms |
| call_duration_seconds | int | Call event metadata | <1ms |
| spoofing_signal | bool | Call event metadata | <1ms |
| answered | bool | Call event metadata | <1ms |
| area_code | str (encoded) | Phone number parsing | <1ms |

### 2. Reputation Features (cached, from Redis)
| Feature | Type | Source | Latency |
|---|---|---|---|
| complaint_count_7d | int | Redis reputation cache | <5ms |
| complaint_count_30d | int | Redis reputation cache | <5ms |
| known_business | bool | Redis reputation cache | <5ms |
| business_verified | bool | Redis reputation cache | <5ms |
| known_scam_cluster | bool | Redis reputation cache | <5ms |
| blocklist_match | bool | Redis reputation cache | <5ms |
| allowlist_match | bool | Redis reputation cache | <5ms |
| first_seen_days_ago | int | Redis reputation cache | <5ms |

### 3. Graph Features (computed, from Neo4j)
| Feature | Type | Source | Latency |
|---|---|---|---|
| complaint_count_graph | int | Neo4j query | <50ms |
| direct_campaign_count | int | Neo4j query | <50ms |
| similar_campaign_count | int | Neo4j query | <50ms |
| community_risk_score | float | Neo4j GDS (precomputed) | <10ms |
| centrality_score | float | Neo4j GDS (precomputed) | <10ms |
| pattern_match_count | int | Neo4j query | <50ms |

## Feature Vector for ML Model

The ML model receives a fixed-width numeric vector of 15 features:

```
[
    call_frequency_24h,      # int
    call_frequency_7d,       # int
    spoofing_signal,         # 0/1
    complaint_count_7d,      # int
    complaint_count_30d,     # int
    known_business,          # 0/1
    business_verified,       # 0/1
    known_scam_cluster,      # 0/1
    blocklist_match,         # 0/1
    allowlist_match,         # 0/1
    first_seen_days_ago,     # int
    answered,                # 0/1
    call_duration_seconds,   # int
    direct_campaign_count,   # int (from graph, 0 if unavailable)
    community_risk_score,    # float (from graph, 0.0 if unavailable)
]
```

## Training-Serving Consistency

### Training Path
```
call_events.csv → feature_extraction.py → feature_vector → XGBoost/LightGBM
```

### Serving Path
```
/score-call request → same feature_extraction logic → same feature_vector → loaded model → probability
```

The `extract_features()` function is shared between training and serving. It lives in `services/ml-risk-service/feature_extraction.py` and is imported by both the training script and the inference wrapper.

## Caching Strategy

| Feature Group | Cache | TTL | Fallback |
|---|---|---|---|
| Metadata | None (real-time) | N/A | Always available from request |
| Reputation | Redis | 1 hour | Default zeros (conservative scoring) |
| Graph | Redis (precomputed) | 30 min | Default zeros (conservative scoring) |

## Future: Online Feature Store

For production scale, migrate to an online feature store (Feast, Tecton, or custom):
- Feature computation runs on Kafka streams
- Features materialized to Redis/DynamoDB
- Training reads from offline store (S3/BigQuery)
- Serving reads from online store (Redis)
- Point-in-time correctness for training data
