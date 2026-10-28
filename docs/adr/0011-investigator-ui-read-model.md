# ADR 0011: Dashboard is a read/presentation layer, not an analytical engine

Status: Accepted

The React application must never duplicate fraud, risk or statistical logic. It consumes server-side read models and submits explicit investigator workflow actions. This prevents browser code from becoming a second source of truth for compliance decisions.
