# Smart Urban Community Resilience System

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)]()
[![License: MIT](https://img.shields.io/badge/license-MIT-green)]()
[![CI](https://img.shields.io/badge/ci-pending-yellow)]()

A CrewAI-powered agentic system for urban emergency management and community resilience. The project monitors, analyzes, and responds to urban incidents via a network of specialized AI agents.

Vision: https://github.com/SMAshhar/CrewAiChallenge-Smart-Urban-Community-Resilience/blob/main/Smart%20Urban%20Community%20Resilience.pdf

---

## ⚠️ NOTE (short)
- This repo contains the **Agentic / GenAI** portion only. Event-driven infra is planned but not fully implemented.
- Some tools (for example the Communicator) are partially implemented — agent calls may be iterative until tool pipelines are completed. We are optimizing for fewer calls.
- Performance: experimental runs show **high token usage** with the current agent traces. See `PERFORMANCE.md` for measured values and mitigations.

---

## 🌟 Features
- Real-time multi-source ingestion (weather, IoT, citizen reports)
- Automated event detection & classification
- Spatial impact assessment and resource prioritization
- Routing & logistics planning for responders
- Multi-channel communications (SMS/email/social drafts)
- Privacy-aware processing & consent management
- Human-in-the-loop validation and continuous learning

---

## 🏗 High-level Architecture

`Data Sources -> Ingest Layer -> Event Bus -> Agent Runtimes (Crews) -> Action & Execution -> Human-in-loop UI -> Storage & ML -> Observability/Security`

### Key components (short)
1. **Data Ingestion Layer**: Collects data from various sources
2. **Processing Pipeline**: Normalizes and validates data
3. **Event Detection System**: Identifies and classifies urban incidents
4. **Response Planning**: Assesses impact and allocates resources
5. **Execution Layer**: Handles logistics and communications
6. **Learning System**: Provides continuous improvement
7. **Privacy Layer**: Ensures data protection and compliance

---

## 🤖 Agents (overview)

**11 specialized agents** — short form. See `docs/agents.md` for configs and detailed I/O.

1. **Feed Collector** — gathers weather, OpenAQ, USGS, MQTT, citizen webhooks → `raw.feeds`.
2. **Data Normalizer & Enricher** — schema validation, geocoding, dedupe → `events.normalized`.
3. **Data Validator** — integrity checks and schema enforcement.
4. **Event Detector & Classifier** — rules + lightweight ML → `events.detected` (type, confidence).
5. **Impact Assessor** — maps affected polygons, population, infra impact → `events.assessed`.
6. **Resource Recommender & Prioritizer** — resource assignments & ETA → `plans.recommended`.
7. **Logistics & Routing Agent** — dispatch routing + commands → `plans.executed`.
8. **Communicator** — formats messages for dashboard, SMS, email, social drafts.
9. **Human-in-the-loop Validator (Incident Commander)** — approval/modification UI.
10. **Learning & Feedback Agent** — creates training datasets, queues retraining.
11. **Privacy & Consent Manager** — PII handling, anonymization, consent audits.

---

## 🚀 Quickstart (dev)

### Prereqs
- Python 3.10+
- Docker & docker-compose (recommended for local dev)
- PostgreSQL + PostGIS (docker-compose included)
- Redis
- Optional: Kafka (or use a lightweight local alternative for testing)

### 1) Clone
```bash
git clone https://github.com/yourusername/smart-urban-resilience.git
cd smart-urban-resilience
```

### 2) Copy environment template

```bash
cp .env.example .env
# Edit .env: POSTGRES_URL, REDIS_URL, MAPBOX_TOKEN, TWILIO_*, CREWAI_API_KEY, KAFKA_URL, SENTRY_DSN
```

### 3) Run the agent crew (dev)

```bash
cd smart_urban_resilience
# into the folder
```

run the crew
```bash
crewai run
```

# 🔐 Security & Privacy

- PII is minimized and anonymized at ingest; consent store enforced by Privacy & Consent Manager.
- Secrets stored in KMS/Vault; TLS enforced for transport; RBAC for dashboards.
- See SECURITY.md for threat model, data retention, and audit procedures.

# 🔄 Reliability Patterns

- Idempotent external commands (idempotency token)
- DLQs & poison message handling
- Circuit breakers on external connectors
- Human gating for critical / low-confidence events
- Versioned rules & canary rollouts

# 📈 Observability & Metrics

- CrewAI Maxim traces for per-agent execution
- Grafana dashboards: ingest rate, processing latency, detection→notification time, DLQ count
- Key SLO: Time from detection → notification (configurable per severity)

# 🧩 Project Layout (short)

.
├── .env.example
├── docker-compose.yml
├── pyproject.toml
├── src/smart_urban_resilience/
│   ├── crew.py
│   ├── main.py
│   ├── config/
│   ├── schema/
│   └── tools/
└── docs/
    ├── agents.md
    ├── PERFORMANCE.md
    └── SECURITY.md

# ✅ Contributing

- Fork
- Create feature branch
- Run tests & linters
- Open PR with description + screenshots + must-pass checks

# 📄 License

MIT — see LICENSE.

# 🙏 Acknowledgments

- My family
- My Abbi and Ammi
- CrewAI framework
- OpenWeather
- OpenAQ
- USGS
- Mapbox
- OSRM.


# 📞 Contact

Syed M. Ashhar — GitHub: SMAshhar — Email: syed.muhammad.ashhar@gmail.com
Project: https://github.com/SMAshhar/CrewAiChallenge-Smart-Urban-Community-Resilience

---

# Extra recommended files to add (quick list)
- `docs/agents.md` (detailed I/O, sample messages, failure modes)
- `PERFORMANCE.md` (measurements + mitigation checklist)
- `SECURITY.md` (threat model + PII flows)
- `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `ISSUE_TEMPLATE.md`, `PULL_REQUEST_TEMPLATE.md`
- `docker-compose.yml` and `scripts/bootstrap.sh`
- `.env.example` with keys/format
- `examples/` containing one runnable synthetic scenario + expected artifacts
---