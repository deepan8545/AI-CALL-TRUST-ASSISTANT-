# Architecture Document — AI Call Trust Assistant

## Design Principle

The system makes fast, reliable, explainable decisions about phone call trustworthiness.

**The most important architectural decision:** The LLM is NOT the primary fraud decision engine. Real-time fraud decisions come from deterministic rules, reputation data, classic ML, and graph intelligence. The LLM explains and summarizes.

## Hybrid Architecture

```
Rules + Reputation + Classic ML + Neo4j Graph = Real-time risk decision
Voice AI + Transcript AI                     = Conversation-level risk signal
LLM                                          = Explanation, summary, reasoning
```

## Service Boundaries

### AI API Backend (FastAPI)
- Main API surface for all clients
- Orchestrates scoring: rules → Redis lookup → ML model → graph features → LLM explanation
- Publishes events to Kafka
- REST for external clients, gRPC-ready for internal service communication

### Event Worker (Go)
- High-throughput Kafka consumer
- Processes scored call events
- Updates Neo4j graph edges
- Triggers feature pipeline
- Writes processed status to PostgreSQL

### Mobile App (React Native)
- Simulates incoming call experience
- Displays caller identity, risk score, risk label, recommendation
- Shows post-call summary
- Consumes backend decisions only — no model logic in the app

### Dashboard (Next.js)
- Call events table with filters
- Risk score distribution and analytics
- High-risk call drill-down
- Verified business directory
- Neo4j fraud cluster visualization

### ML Risk Service
- Rules baseline scoring
- XGBoost/LightGBM model inference
- Feature extraction and preprocessing
- MLflow/W&B experiment tracking
- Feature store design for training-serving consistency

### LLM Summary Service
- Provider abstraction: Claude, OpenAI GPT, Gemini, local models, mock
- Prompt templates for explanation, summary, intent extraction
- JSON output schema validation
- Guardrails: LLM explains structured signals, does not make fraud decisions

### Voice AI Service
- Speech-to-text provider interface
- Voice embedding provider interface
- Synthetic voice detection interface (placeholder for MVP)
- Scam phrase and intent detection

## Data Flow

```
Incoming Call → FastAPI /score-call
  ├── Redis: reputation lookup (ms latency)
  ├── Rules Engine: deterministic scoring
  ├── ML Model: XGBoost/LightGBM probability
  ├── Neo4j: graph risk features
  ├── Transcript Analyzer: scam phrase detection
  └── LLM: explanation generation
        │
        ▼
  Risk Score + Label + Reason Codes + Explanation
        │
        ├── → Response to client
        ├── → PostgreSQL (store decision)
        ├── → Kafka call.scored topic
        └── → Redis (update cache)
```

## Technology Choices

| Component | Technology | Why |
|---|---|---|
| Real-time scoring | Rules + XGBoost/LightGBM | Fast, cheap, explainable, strong for tabular fraud data |
| Graph intelligence | Neo4j + Graph Data Science | Fraud is a relationship problem — scam networks share patterns |
| Reputation cache | Redis | Millisecond lookups required for real-time call scoring |
| Event streaming | Kafka | Continuous call events feed scoring, graph, analytics, training |
| Product database | PostgreSQL | Reliable transactional storage for core product data |
| Vector search | pgvector (MVP) → Pinecone/Weaviate | Semantic matching of scam transcripts against known patterns |
| LLM providers | Claude + GPT + Gemini + local | Provider abstraction — right model for each task |
| Voice AI | Hugging Face + cloud speech | Pretrained models for STT, embeddings, future deepfake detection |
| Infrastructure | Docker + K8s + Terraform | Production-grade deployment path from day one |
