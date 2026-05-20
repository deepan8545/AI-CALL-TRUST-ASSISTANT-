# Event Worker (Go)

High-throughput Kafka consumer that processes scored call events, writes to PostgreSQL, and will update Neo4j graph edges.

**Status:** Built — Day 5

## How It Works
1. Consumes `call.scored` topic from Kafka
2. Parses scored call events (call_id, risk_score, risk_label, reason_codes)
3. Writes processed decision to `model_decisions` table in PostgreSQL
4. Logs every processed event with count
5. Graceful shutdown on SIGINT/SIGTERM

## Running Locally
```bash
# Via Docker Compose (recommended)
cd infrastructure/docker
docker compose up event-worker

# Standalone (requires Go 1.22+)
go run main.go
```

## Environment Variables
| Variable | Default | Description |
|---|---|---|
| `KAFKA_BOOTSTRAP_SERVERS` | `localhost:9092` | Kafka broker address |
| `KAFKA_TOPIC_CALL_SCORED` | `call.scored` | Topic to consume |
| `KAFKA_CONSUMER_GROUP` | `event-worker-group` | Consumer group ID |
| `DATABASE_URL` | `postgres://...localhost:5432/call_trust` | PostgreSQL DSN |
