# Risk Scoring Engine

Milestone 6 turns rule findings into prioritized risk assessments.

## Why scoring is needed

A single rule hit is not enough for investigation prioritization. Multiple weak signals can matter more than one isolated event, and repeated duplicate hits need damping to avoid noisy rules dominating the result.

## Risk bands

| Score | Level |
|------:|-------|
| 0-20 | normal |
| 21-40 | review |
| 41-60 | suspicious |
| 61-80 | high_risk |
| 81-100 | critical |

## Scoring rules

- First occurrence of a rule gets full score.
- Duplicate occurrences are dampened.
- Critical + high combinations receive escalation.
- Multiple findings receive escalation.
- Final score is capped at 100.

## Output

A `RiskAssessment` contains:

- entity type
- entity id
- risk score
- risk level
- summary
- triggered rules
- top reasons

## Legal/HR note

Risk scoring indicates investigation priority. It is not a legal determination of fraud.
