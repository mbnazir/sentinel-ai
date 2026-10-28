# ADR-0001: Clean Architecture boundary

Status: Accepted

Sentinel domain and application contracts must not depend on FastAPI, SQLAlchemy, Redis, Quartz, or a specific LLM provider. External systems are adapters. This prevents Quartz-specific concepts from contaminating the integrity engine and allows future connectors to normalize into the same contracts.
