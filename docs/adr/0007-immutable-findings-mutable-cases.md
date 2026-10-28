# ADR 0007: Immutable analytical findings, mutable investigation workflow

Status: Accepted

Analytical output is evidence and must remain reproducible. Investigator workflow is human state and must evolve.

Therefore durable findings are append-only and hash-protected. Cases reference findings and may change assignment, status, notes and disposition. A rule-engine change requires a new scan version; historical findings are never rewritten.

This separation supports audit defensibility, model/rule version comparison, false-positive analysis and future AI summaries without corrupting source evidence.
