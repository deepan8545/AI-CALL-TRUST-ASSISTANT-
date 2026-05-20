# Neo4j Graph Data Model

## Node Labels

- `PhoneNumber` — individual phone numbers (hashed)
- `Business` — verified or unverified business entities
- `Carrier` — telecom carriers
- `UserSegment` — groups of call recipients
- `CallEvent` — individual call occurrences
- `Complaint` — user-reported complaints
- `ScamPattern` — known scam behavior patterns
- `ScamCampaign` — coordinated scam campaigns
- `Region` — geographic regions
- `TranscriptSignal` — detected transcript-level signals

## Relationships

- `(:PhoneNumber)-[:CALLED]->(:UserSegment)`
- `(:PhoneNumber)-[:BELONGS_TO]->(:Business)`
- `(:PhoneNumber)-[:USES_CARRIER]->(:Carrier)`
- `(:PhoneNumber)-[:REPORTED_IN]->(:Complaint)`
- `(:PhoneNumber)-[:MATCHES_PATTERN]->(:ScamPattern)`
- `(:PhoneNumber)-[:PART_OF_CAMPAIGN]->(:ScamCampaign)`
- `(:CallEvent)-[:FROM_NUMBER]->(:PhoneNumber)`
- `(:CallEvent)-[:HAS_TRANSCRIPT_SIGNAL]->(:TranscriptSignal)`
- `(:Business)-[:VERIFIED_BY]->(:Carrier)`
- `(:PhoneNumber)-[:SIMILAR_BEHAVIOR_TO]->(:PhoneNumber)`
- `(:ScamCampaign)-[:TARGETS_REGION]->(:Region)`

## Graph-Derived Features

| Feature | Description |
|---|---|
| `number_degree` | Total connections for a phone number |
| `complaint_degree_7d` | Complaints in the last 7 days |
| `campaign_cluster_id` | ID of the scam campaign cluster |
| `community_risk_score` | Risk score of the number's community |
| `pagerank_score` | PageRank centrality in the call graph |
| `similarity_to_known_scam` | Behavioral similarity to known scam numbers |
| `shared_target_segments` | Overlap in targeted user segments |
| `carrier_risk_score` | Risk score of the carrier |
| `business_verification_distance` | Hops to nearest verified business |

## Example Cypher Query

```cypher
MATCH (p:PhoneNumber {phone_number_hash: $phone_number_hash})
OPTIONAL MATCH (p)-[:PART_OF_CAMPAIGN]->(c:ScamCampaign)
OPTIONAL MATCH (p)-[:REPORTED_IN]->(r:Complaint)
OPTIONAL MATCH (p)-[:SIMILAR_BEHAVIOR_TO]->(other:PhoneNumber)-[:PART_OF_CAMPAIGN]->(oc:ScamCampaign)
RETURN
  p.phone_number_hash AS phone_number_hash,
  count(DISTINCT r) AS complaint_count,
  count(DISTINCT c) AS direct_campaign_count,
  count(DISTINCT oc) AS similar_campaign_count,
  p.reputation_score AS reputation_score
```
