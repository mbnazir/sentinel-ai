# Milestone 13 - AI Investigator and Local Quartz UAT

Sentinel AI v0.13.0 adds an evidence-grounded AI Investigator with provider abstraction for Gemini and OpenAI-compatible APIs, immutable AI input hashes, prompt versioning, persisted summaries, and audit events.

The milestone also closes local deployment gaps:
- working backend Docker build order
- Celery task module registration
- scan auto-enqueue
- scan cancellation endpoint
- in-container local JWT generator
- token entry screen in the React UI
- end-to-end Quartz runner
- full local deployment runbook
- Quartz REST contract and UAT sequence

AI is downstream of deterministic findings. It cannot create, edit, or delete integrity evidence.
