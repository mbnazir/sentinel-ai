# ADR 0009: Durable chunks and population-level finalization

Status: Accepted

Employee-day deterministic analysis is chunkable and idempotent. Behavioral and organizational analytics are population-level computations and must not be independently evaluated inside arbitrary worker chunks.

Therefore phase 1 workers persist deterministic findings per employee-day. After all chunks complete, a finalization phase may calculate behavioral and organizational findings using the complete scan population. This prevents chunk boundaries from changing statistical results.
