# System Design — Unified Document Viewer (Scenario D)

## 1. Problem & Scope

A dealership user (e.g. a salesperson closing a deal) needs every document related to a
vehicle in **one place**, even though those documents live in **two separate dealership
systems** (a Sales system and a Service system). Today they must look in both systems and
stitch the results together by hand.

This service exposes a single endpoint: enter a **VIN**, get back **one consolidated list**
of documents from both systems, each item clearly tagged with its source.

**In scope (V1):** unified VIN search; parallel calls to both sources; merged, source-tagged
list; graceful degradation when a source is unavailable; persistent audit log; structured logging.

**Out of scope (designed for, not built):** authentication, multi-tenancy (per-dealership data
isolation), result caching, an in-app file viewer. These are realistic next steps; the
architecture leaves room for them (see §7).

**Layer built:** Backend. The client layer is mocked (test harness / cURL). The external Sales
and Service systems are mocked by a small local server (`mocks/mock_servers.py`).

---

## 2. Architecture

```
        Client (cURL / test harness)
                  │  GET /api/vehicles/<vin>/documents
                  ▼
   ┌────────────────────────────────────────────────────────┐
   │                      Backend (Django)                    │
   │                                                          │
   │   Controller (views.py)                                  │
   │     • validate VIN  • map 200/502  • write audit log     │
   │                  │                                        │
   │                  ▼                                        │
   │   Aggregator (aggregator.py)                             │
   │     fan-out (ThreadPoolExecutor) → fan-in (merge+tag)    │
   │            │                     │                        │
   │     fetch_sales            fetch_service   (adapters/ACL) │
   │            │                     │                        │
   └────────────┼─────────────────────┼───────────────────────┘
                ▼                     ▼
        Sales System API     Service System API     (mocked: :9001 / :9002)

   SQLite ← SearchAuditLog (vin, timestamp, per-source status, doc count)
   Structured logging at every step (stdout)
```

### Component roles
| Component | Responsibility |
|-----------|----------------|
| **Controller** (`documents/views.py`) | HTTP only: validate the VIN, call the aggregator, map the result to 200/502, write the audit log. |
| **Aggregator** (`documents/aggregator.py`) | Business logic: fan out to both sources concurrently, merge the results, tag each document with its source, decide overall outcome. |
| **Adapters** (`fetch_sales` / `fetch_service`) | Anti-Corruption Layer: call one external system and translate its response into the shared `Document` model; swallow failures into a per-source status. |
| **External APIs** (mocked) | Stand-ins for the real Sales and Service systems; each speaks its own field language. |
| **SearchAuditLog** (SQLite) | Records each lookup and per-source outcome for observability. |

---

## 3. Data Flow

A request to `GET /api/vehicles/<vin>/documents`:

1. Controller validates the VIN (must be 17 chars) → `400` if invalid.
2. Controller calls `aggregate_documents(vin)`.
3. Aggregator submits `fetch_sales` and `fetch_service` to a `ThreadPoolExecutor` — both run **concurrently**.
4. Each adapter calls its API (`requests.get`, with a timeout), then translates the payload into `Document`s.
   - On success → `(documents, SourceResult(ok))`.
   - On any failure (timeout, connection error, bad payload) → `([], SourceResult(unavailable, error))`. The exception is caught inside the adapter so it can never crash the request.
5. Aggregator merges all returned documents into one list and collects the two `SourceResult`s into `sources`.
6. Controller maps the outcome: **200** if at least one source responded, **502** only when every upstream failed.
7. Controller writes a `SearchAuditLog` row (best-effort; a logging failure never affects the response).

**Latency:** because the two calls run concurrently, total time is bounded by the slower
source, not the sum of both.

### API contract
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

---

## 4. Tech Stack & Justifications

| Layer | Choice | Why |
|-------|--------|-----|
| Language / framework | Python + Django REST Framework | Familiarity (ship within the time budget); batteries included: routing, serialization, test client. |
| Concurrency | `concurrent.futures.ThreadPoolExecutor` | The work is **I/O-bound** with only **two** calls. Threads give true concurrency for blocking HTTP without the complexity of an async stack. Async would matter at hundreds/thousands of concurrent calls (see §7). |
| HTTP client | `requests` | Simple, synchronous, pairs naturally with threads. |
| Database | SQLite (Django ORM) | The app doesn't own the documents; it only persists a lightweight audit log. SQLite is enough for V1 and trivially swappable for Postgres in production. |
| Tests | Django test runner (`unittest` + `unittest.mock`) | Core logic is tested without the network by mocking the adapters / `requests`. |

---

## 5. Key Design Decisions

- **Build the backend, mock the client.** Scenario D's hard part — concurrent aggregation and
  partial-failure handling — lives server-side, so the backend is where the design is exercised.
- **Threads over async (for now).** I/O-bound + two sources → threads are sufficient and keep the
  familiar DRF stack. The choice is revisited only if the source count grows.
- **Partial-failure response contract.** Data (`documents`) is kept separate from per-source
  health (`sources`). A failed source becomes a status entry, never a fake/empty document. HTTP
  status distinguishes the two cases that must not look alike: *vehicle has no documents*
  (`200`, empty list, sources ok) vs *all upstreams down* (`502`).
- **Adapters as an Anti-Corruption Layer.** Each external system speaks its own field language;
  a per-source translator maps it into the shared `Document`. If a source changes its format,
  only its adapter changes.
- **Configurable timeout (default 5s).** A slow source is as harmful as a dead one for a waiting
  user, so every call has a timeout; on timeout the source is marked unavailable. The value is
  read from the environment and tunable against real latency.
- **Audit log shape.** Two fixed sources → two atomic status columns (1NF-clean, easy to query).
  If sources became dynamic/numerous, this would normalize into a child table (1:N).
- **Single-file aggregator.** With two fixed sources the adapter *role* is kept as functions in
  one module rather than a separate package — simpler to read without losing the separation of
  concerns between HTTP and business logic.

---

## 6. Observability

- **Logging:** structured logs (`{timestamp} {level} {logger} {message}`) on every search and on
  every source failure, emitted to stdout via Python's `logging.config.dictConfig`. In production
  the handler swaps to a file or log aggregator without touching application code.
- **Audit log:** `SearchAuditLog` captures VIN, timestamp, per-source status and document count —
  a foundation for usage analytics and "which source fails most / when" dashboards.
- **Metrics & tracing (next):** request latency and per-source success-rate counters; distributed
  tracing across the two upstream calls would make the fan-out visible end-to-end.

---

## 7. Scalability & Future Work

- **Auth & multi-tenancy:** add an authenticated user and a per-dealership scope; the audit log
  already anticipates a `searched_by` field.
- **Caching:** cache aggregated results per VIN (short TTL) for repeat lookups during multi-day
  sales cycles; a cache layer slots in front of the aggregator.
- **More sources:** generalize the two adapter functions into an `adapters/` package and iterate
  over a registry; for many concurrent sources, move from threads to async I/O.
- **Resilience:** retries with backoff and a circuit breaker per source.

---

## 8. How GenAI Was Used in the Design Phase

The design was developed with an AI collaborator used in a **Socratic** mode rather than as a
code generator. The work followed an SDLC sequence — requirements → system design → data model →
implementation — where the AI asked questions to pressure-test each decision instead of handing
over answers. Every significant choice (backend-vs-frontend, threads-vs-async, the partial-failure
contract, persistence shape, timeout policy) was recorded as a decision with its alternatives and
trade-offs. The AI scaffolded boilerplate and reviewed code; the core logic (fan-out/fan-in, the
adapters, degradation handling) was written and owned by me, and verified by running the service
against mock sources and by automated tests — including a test that simulates a downed source to
prove graceful degradation.
