# Investigation Case Management

Milestone 8 introduces investigation case management.

## Purpose

Risk scores are not enough. Compliance teams need a controlled workflow to review, assign, comment, and close cases.

## Case lifecycle

```text
new
  -> triaged
  -> assigned
  -> in_review
  -> needs_more_info
  -> substantiated / unsubstantiated
  -> closed
```

## Case contents

An investigation case contains:

- case id
- organization id
- entity type
- entity id
- risk score
- priority
- status
- assignee
- summary
- evidence links
- comments

## Important

A case status of `substantiated` means the internal investigation found supporting evidence. It still should not be treated as a legal conclusion without HR/legal review.

## Next

Milestone 9 should add persistence-backed case repositories and API operations or move into AI investigation summaries depending on priorities.
