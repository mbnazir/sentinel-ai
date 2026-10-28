# ADR 0013: AI Investigator is evidence-grounded and non-authoritative

Status: Accepted

The LLM receives only Sentinel case metadata and persisted deterministic/behavioral/organizational findings. It is instructed not to declare fraud or guilt and not to invent missing facts.

Every generated brief stores provider, model, prompt version and SHA-256 input hash. Generation is written to the case audit trail.

AI output is investigator assistance, never the source of truth. Rule findings, evidence hashes and human case dispositions remain authoritative.
