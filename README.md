# AI Call Trust Assistant — MVP

A real-time trust engine for phone calls. Scores every call, explains why it's safe or risky, detects fraud networks via graph intelligence, and summarizes calls in plain English.

## Architecture Overview

```
React Native Mobile App ──► FastAPI AI Backend ──► PostgreSQL
React/Next.js Dashboard ──►     │                  Redis
                                │                  Kafka
                                ├──► Neo4j Graph Intelligence
                                ├──► ML Risk Service (XGBoost/LightGBM)
                                ├──► Voice AI Service
                                ├──► LLM Summary Service (Claude/GPT/Gemini)
                                └──► Vector Search (pgvector)
```

## Services

| Service | Path | Tech | Purpose |
|---|---|---|---|
| **AI API Backend** | `services/ai-api-fastapi` | Python, FastAPI | Main API surface — scores calls, analyzes transcripts, requests ML/graph/LLM services |
| **Event Worker** | `services/event-worker-go` | Go | High-throughput Kafka consumer, writes to PostgreSQL and Neo4j |
| **Mobile App** | `services/mobile-app` | React Native, TypeScript | Incoming call simulation, risk display, post-call summary |
| **Dashboard** | `services/dashboard` | React, Next.js, TypeScript | Call events, risk analytics, fraud graph view, verified businesses |
| **LLM Summary Service** | `services/llm-summary-service` | Python | Provider abstraction for Claude, OpenAI, Gemini, local models |
| **Voice AI Service** | `services/voice-ai-service` | Python | Speech-to-text, voice embeddings, synthetic voice detection (interfaces) |
| **ML Risk Service** | `services/ml-risk-service` | Python | XGBoost/LightGBM training, inference, MLflow/W&B tracking |

## Data Stores

| Store | Purpose |
|---|---|
| **PostgreSQL** | Core product data — businesses, call events, risk scores, summaries, scam patterns |
| **Redis** | Low-latency reputation cache — number reputation, business identity, scam clusters |
| **Kafka** | Event streaming — call events, scored calls, transcripts, fraud feedback, graph updates |
| **Neo4j** | Graph intelligence — phone number relationships, fraud clusters, community detection |
| **pgvector** | Vector search — scam transcript embeddings, similar pattern retrieval |

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/score-call` | Score an incoming call for fraud risk |
| `POST` | `/ingest-call-event` | Ingest a raw call event |
| `POST` | `/analyze-transcript` | Analyze transcript for scam phrases/intent |
| `POST` | `/summarize-call` | Generate call summary with LLM |
| `POST` | `/graph-risk` | Get graph-derived risk features from Neo4j |
| `GET` | `/calls` | List recent call events |

## Quick Start

```bash
# Start the FastAPI backend locally
cd services/ai-api-fastapi
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Run tests
pytest tests/ -v
```

## Environment Variables

See `.env.example` for all required configuration.

## Documentation

- `docs/architecture.md` — Full architecture document
- `docs/api-contracts.md` — Detailed API contracts with examples
- `docs/neo4j-graph-model.md` — Graph data model and Cypher queries
- `docs/data-strategy.md` — Data gathering and privacy rules
- `docs/feature-store-design.md` — Feature engineering and store design (Week 2)

## 4-Week Sprint Plan

- **Week 1**: Foundation — repo, FastAPI, PostgreSQL, Redis, Kafka, rule-based scoring
- **Week 2**: Intelligence — Neo4j graph, synthetic data, XGBoost/LightGBM, MLflow
- **Week 3**: AI Layer — transcript analysis, LLM summaries, vector search, frontends
- **Week 4**: Production — observability, CI/CD, Terraform, K8s, demo, pitch
