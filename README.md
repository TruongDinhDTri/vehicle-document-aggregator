# Unified Document Viewer — Keyloop Technical Assessment (Scenario D)

A backend service that gathers all documents for **one vehicle** from **two separate dealership
systems** (Sales + Service) into **one consolidated list**, searchable by **VIN**.

- **Fan-out / fan-in** — both sources are called **concurrently** (`ThreadPoolExecutor`).
- **Graceful degradation** — if one source is down, the other's documents are still returned and
  the failed source is reported.
- **Anti-Corruption Layer** — each source has an adapter that normalizes its response into one shared model.

> Architecture and the reasoning behind each decision: see [`SYSTEM_DESIGN.md`](./SYSTEM_DESIGN.md).

---

## How it fits together

There are **three** processes. The app you query runs on port **8000**. Behind it, the app calls
**two mock external APIs** on ports **9001** (Sales) and **9002** (Service) — these stand in for
the real dealership systems. You therefore need **two terminals**, and the virtualenv must be
**activated in each one**.

```
client → :8000 (this app) → :9001 (Sales mock)
                          → :9002 (Service mock)
```

---

## Prerequisites
- Python 3.11+ (developed on 3.13)

## Setup (once)
```bash
git clone <repo-url>
cd vehicle-document-aggregator

python3 -m venv venv
source venv/bin/activate            # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate            # creates SQLite + the audit-log table
```

## Run the app

**Terminal A — start the two mock external APIs:**
```bash
source venv/bin/activate
python mocks/mock_servers.py        # Sales on :9001, Service on :9002 (leave it running)
```

**Terminal B — start the API server:**
```bash
source venv/bin/activate
python manage.py runserver 8000
```

**Query it (any terminal):**
```bash
# Happy path → 200, four documents merged from both sources, each tagged with its source
curl http://localhost:8000/api/vehicles/WDB4631234567890X/documents

# Unknown (but valid) VIN → 200 with an empty list (the vehicle simply has no documents)
curl http://localhost:8000/api/vehicles/ZZZ9999999999999Z/documents

# Invalid VIN (not 17 chars) → 400
curl http://localhost:8000/api/vehicles/SHORTVIN12345678/documents
```

**Demo graceful degradation** (point the Service source at a dead port; Sales stays up):
```bash
SERVICE_API_URL=http://localhost:9099 python manage.py runserver 8000
curl http://localhost:8000/api/vehicles/WDB4631234567890X/documents
# → still HTTP 200: only Sales documents, and
#   sources contains { "source": "SERVICE", "status": "unavailable", "error": ... }
```
> If you forget to start the mocks, both sources are unreachable and the endpoint returns **502**
> (all upstreams down) — which is the intended behavior, not a bug.

## Run the tests
```bash
source venv/bin/activate
python manage.py test
```
Tests live in `documents/tests.py` and cover the core business logic — the 200/502 decision,
fan-in/merge, graceful degradation, and adapter field translation — all without the network.

---

## API contract
```
GET /api/vehicles/<vin>/documents
  200 → at least one source responded (degradation reported in `sources`)
  502 → all upstream sources failed
  400 → VIN is not 17 characters
```
```jsonc
{
  "vin": "WDB4631234567890X",
  "documents": [
    { "id", "vin", "title", "document_type", "issued_date", "source", "document_url" }
  ],
  "sources": [
    { "source": "SALES",   "status": "ok" },
    { "source": "SERVICE", "status": "unavailable", "error": "..." }
  ]
}
```

## Project structure
```
config/                 # Django project (settings: env-based source config, timeout, logging)
documents/
  views.py              # Controller — validate VIN, map 200/502, write audit log
  aggregator.py         # Aggregator + adapters — fan-out/fan-in, translation, degradation
  models.py             # SearchAuditLog (observability)
  tests.py              # core business-logic tests
mocks/mock_servers.py   # two mock external APIs (each with its own field language)
SYSTEM_DESIGN.md        # architecture, data flow, decisions, observability
```

---

## AI Collaboration Narrative

I worked with an AI assistant (Claude) as a **design partner and accelerator** — I set the
direction and owned the outcome; the AI sharpened my thinking and sped up the mechanical work.

- **Strategy for directing the AI.** I drove the work through a deliberate sequence — requirements,
  system design, data model, then implementation — and used the AI primarily to *pressure-test*
  decisions: "here's my reasoning, find the holes," and "what are the alternatives and trade-offs
  I'm missing?" Every significant choice (backend vs frontend, threads vs async, the 200/502
  partial-failure contract, what to persist, the timeout policy) is captured as a decision record
  with its alternatives and trade-offs, so each one is mine to defend.
- **Ownership of the solution.** The core logic — the concurrent fan-out/fan-in, the per-source
  adapters that normalize each system's payload, and the graceful-degradation handling — is my
  design and my code. I used the AI to scaffold boilerplate and as a reviewer, then shaped the
  result to fit the architecture rather than accepting it as-is.
- **Verifying & refining its output.** I treated nothing as done until I had seen it work and
  could explain it. Every piece was validated three ways: static checks (`python manage.py check`),
  a live `curl` matrix against the mock sources (happy path, empty result, bad input, a simulated
  source outage, and total outage), and automated tests — including one that simulates a downed
  source to prove graceful degradation. Where the AI's first suggestion was wrong or over-built
  (e.g. an over-structured layout for only two sources), I simplified it deliberately.
- **Ensuring final quality.** The repository is kept clean and reproducible: a thin HTTP layer
  separated from business logic, a tested core, and setup/run instructions a reviewer can follow
  in minutes. The reasoning behind the design lives in `SYSTEM_DESIGN.md`.
