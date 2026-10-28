# Milestone 11 - Investigator Dashboard and Case Workspace

Adds a React + TypeScript investigator application backed by Sentinel APIs.

Primary views:
- Integrity Overview
- Findings Queue
- Finding Evidence Detail
- Investigation Queue
- Case Workflow and Audit History
- Scan Operations

The frontend does not calculate risk. It renders backend-produced findings and case state only.

Dashboard APIs:
- GET /api/v1/dashboard/overview
- GET /api/v1/dashboard/findings
- GET /api/v1/dashboard/findings/{finding_id}
- GET /api/v1/dashboard/cases
- GET /api/v1/dashboard/scans

Case workflow continues through the existing investigation APIs.

The UI deliberately labels findings as analytical signals, not fraud determinations.
