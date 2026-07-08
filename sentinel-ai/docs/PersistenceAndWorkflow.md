# Persistence-backed Repositories and Workflow APIs

Milestone 10 wires the earlier domain services into persistence-backed workflows.

## Added persistence tables

- investigation_cases
- investigation_evidence_links
- investigation_comments
- investigation_narratives

## Added repositories

- InvestigationRepository
- NarrativeRepository

## Added workflow service

`InvestigationWorkflowService` coordinates case assignment, transitions, comments, and AI narrative generation.

## API

Workflow APIs are available under:

```text
/api/v1/workflow
```
