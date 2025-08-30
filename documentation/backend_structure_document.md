# Backend Structure Document

## 1. Backend Architecture

This project follows a clean, service-oriented design that keeps each part of the server focused and easy to update. Here’s how it’s set up:

- **Language & Framework**
  - Python 3.9+ with FastAPI for building async HTTP endpoints quickly.
  - gRPC (via grpcio and Protobuf) alongside REST so clients can choose the fastest protocol.
- **Server Model**
  - ASGI server (Uvicorn or Hypercorn) to handle thousands of connections without blocking.
  - Layered code organization:
    - **API layer** handles input/output and validation.
    - **Service layer** implements business rules (message routing, doc lookup).
    - **Config layer** loads settings (YAML, env vars).
- **Design Patterns**
  - Dependency injection (built into FastAPI) keeps components loosely coupled.
  - Clear separation of concerns: authentication, message flows, and documentation serving each live in their own modules.

How this supports our goals:
- **Scalability**: Stateless services can run multiple replicas behind a load balancer.
- **Maintainability**: Well-defined layers and DI make it easy to add features or swap implementations.
- **Performance**: Async I/O plus gRPC support keeps response times low, even under heavy load.

---

## 2. Database Management

Version 1.0 does not use a traditional database. Data handling is as follows:

- **In-Memory Stores**
  - **Client registry** and **message queue** live in Python data structures for maximum speed.
  - All data resets if the server restarts.
- **File System**
  - Documentation files (HTML, Markdown) are read directly from a mounted `docs/` folder.
- **Future Options**
  - For persistence or clustering, a NoSQL store like Redis or an SQL system (e.g., PostgreSQL) can be added.
  - These external stores would hold client info, queued messages, and metadata for versioned docs.

---

## 3. Database Schema (In-Memory Data Structures)

Because we’re not using a formal DB, here’s a human-readable outline of our key data objects:

• **Client Registry**  
  • `client_id` (string): Unique identifier for each process  
  • `group_id` (string): The communication group the client belongs to  
  • `last_heartbeat` (timestamp): When the client last checked in  

• **Message Queue**  
  • `message_id` (string): Unique ID for each message  
  • `sender_id` (string): `client_id` of the sender  
  • `group_id` (string): Target group for routing  
  • `payload` (string or JSON): Actual message content  
  • `timestamp` (timestamp): When the message was accepted  

• **Documentation Files**  
  • Stored as files under `/docs/{version}/…`  
  • No metadata table; version folders imply release numbers.

If we switch to an SQL database later, the tables might look like this (PostgreSQL syntax):

```sql
CREATE TABLE clients (
  client_id   TEXT PRIMARY KEY,
  group_id    TEXT NOT NULL,
  last_heartbeat TIMESTAMP NOT NULL
);

CREATE TABLE messages (
  message_id  TEXT PRIMARY KEY,
  sender_id   TEXT NOT NULL REFERENCES clients(client_id),
  group_id    TEXT NOT NULL,
  payload     JSONB NOT NULL,
  timestamp   TIMESTAMP NOT NULL
);
```

---

## 4. API Design and Endpoints

We expose both REST and gRPC interfaces so clients can pick what works best.

### REST Endpoints (FastAPI)

- **POST /login**  
  Authenticates a user or service account, returns a JWT token.

- **POST /mcp/register**  
  Registers a client in a group. Body: `client_id`, `group_id`.

- **POST /mcp/send**  
  Sends a message. Body: `sender_id`, `group_id`, `payload`.

- **GET /mcp/receive**  
  Polls for new messages. Query: `client_id`, `group_id`.

- **GET /docs/{version}/{path}**  
  Serves static documentation files from the configured folder.

- **GET /health**  
  Returns `200 OK` if the server is running.

- **GET /metrics**  
  Prometheus-style metrics (request counts, error counts, latencies).

### gRPC Methods (proto files)

- **RegisterClient(Request) → Ack**  
  Mirrors `/mcp/register` for low-latency registration.

- **SendMessage(Request) → Ack**  
  Mirrors `/mcp/send` using HTTP/2.

- **ReceiveMessages(Request) → MessageList**  
  Mirrors `/mcp/receive`, streaming replies if desired.

All REST and gRPC calls require a valid JWT in an `Authorization: Bearer <token>` header (or metadata).  

---

## 5. Hosting Solutions

We package the server in a Docker container so it can run anywhere Docker is supported. Typical hosting options:

- **Development & Small Deployment**: Docker Compose on a single VM or physical machine.
- **Production & Scaling**: Kubernetes (EKS, GKE, AKS) or any cloud-native container service.

Benefits:
- **Reliability**: Containers isolate dependencies, preventing environment drift.
- **Scalability**: Add or remove replicas without downtime behind a load balancer.
- **Cost-Effectiveness**: Pay only for the compute you use; spin down non-critical replicas during low traffic.

---

## 6. Infrastructure Components

To deliver fast, reliable service, we layer in these pieces:

- **Load Balancer**  
  - NGINX or cloud-native LB (AWS ALB/GCP LB) distributes traffic evenly.

- **Caching**  
  - HTTP cache headers for static docs.  
  - Optional Redis or in-process LRU cache for popular pages.

- **Content Delivery Network (CDN)**  
  - Services like AWS CloudFront or Fastly to cache and serve docs closer to users.

- **Logging & Aggregation**  
  - JSON-formatted logs (structlog or Python logging) sent to ELK/EFK or CloudWatch Logs.

- **Secrets Management**  
  - Store JWT keys and sensitive config in AWS Secrets Manager, HashiCorp Vault, or Kubernetes Secrets.

These components work together to balance load, reduce latency, and keep our logs and secrets safe and accessible.

---

## 7. Security Measures

We protect both data and endpoints at multiple layers:

- **Transport Security**  
  - TLS everywhere (HTTPS for REST, TLS in gRPC).  
  - Redirect HTTP to HTTPS automatically.

- **Authentication & Authorization**  
  - JWT tokens with short expiry (15 minutes) issued by `/login`.  
  - Role checks (reader vs. writer) on each MCP and docs endpoint.

- **Input Validation**  
  - FastAPI’s built-in Pydantic schemas prevent malformed or malicious payloads.

- **Audit Logging**  
  - Record every login attempt, message send/receive, and doc access for forensic analysis.

- **Rate Limiting (Future Phase)**  
  - Middleware to throttle abusive clients and protect against denial-of-service.

---

## 8. Monitoring and Maintenance

Keeping the backend healthy involves both real-time alerts and regular upkeep:

- **Monitoring Tools**  
  - Prometheus scrapes `/metrics` for key stats (request rate, error rate, latencies).  
  - Grafana dashboards display trends and trigger alerts when thresholds are crossed.

- **Health Checks & Alerts**  
  - Kubernetes or the load balancer probes `/health`.  
  - PagerDuty or Slack alerts for failing health checks or high error rates.

- **Logging & Tracing**  
  - Centralized log store with query capability (Elasticsearch, Datadog).  
  - Distributed tracing (OpenTelemetry) can be added in later versions.

- **Maintenance Practices**  
  - CI/CD pipeline (GitHub Actions) enforces linting, tests, and safe rollouts.  
  - Automated dependency updates via Dependabot or Renovate.  
  - Scheduled restarts or graceful restarts after config changes.

---

## 9. Conclusion and Overall Backend Summary

The **Nvidia-docs-MCP-server** backend is designed for simplicity today and easy growth tomorrow. By combining:

- **FastAPI + gRPC** for flexible, high-speed communication
- **In-memory data stores** and file-based docs for rapid development
- **Containerization & cloud orchestration** for reliable scaling
- **TLS, JWT, and structured logging** for robust security and auditing
- **Prometheus/Grafana monitoring** for real-time visibility

we meet our goals of sub-100 ms message round-trips, sub-50 ms doc loads, and 99.9% uptime. This structure keeps the team productive, operations smooth, and users happy—while leaving room to add databases, rate limiting, and advanced GPU integrations in future releases.