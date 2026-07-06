# Timeline Reconstruction Engine

Milestone 3 introduces Sentinel AI's timeline reconstruction layer.

## Purpose

Fraud and integrity issues usually happen at activity level, not only at session-total level.

The timeline engine converts activities from different source versions into atomic comparable intervals.

| ID | Source |
|---:|--------|
| 0 | Phone |
| 1 | System |
| 2 | Agent |
| 3 | Supervisor |
| 4 | Manager |
| 5 | Payroll |

## Example

System:

```text
08:00-09:00 Work
```

Agent:

```text
08:00-09:30 Work
```

Output:

```text
08:00-09:00 System + Agent
09:00-09:30 Agent only
```

That second segment is direct evidence of manual extension.

## Included

- DataSource
- ActivitySnapshot
- TimelineSegment
- Timeline
- TimelineBuilder
- TimelineComparator
- ActivitySnapshotMapper
- Timeline API scaffold
- Unit tests

## Next

Milestone 4: Activity Matching Engine.
