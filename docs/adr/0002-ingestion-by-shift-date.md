# ADR-0002: Shift-date range is the primary ingestion boundary

Status: Accepted

Sentinel ingests workforce records over inclusive shift-date ranges. A login session is not treated as an isolated analytical unit. All sessions belonging to an agent on the same shift date are preserved, including multiple login sessions, because repeated edits, manager-added sessions, abnormal shutdowns, overlaps, and collusion patterns can only be evaluated correctly across the employee-day context.
