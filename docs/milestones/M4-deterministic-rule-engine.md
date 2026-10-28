# Milestone 4 - Deterministic Integrity Rule Engine and Risk Scoring

Sentinel now converts neutral timeline evidence into explainable integrity findings at the `agent + shift_date` grain.

## Rule contract
Every rule produces zero or more immutable `RuleFinding` values containing:

- stable rule ID and name
- category and severity
- evidence confidence
- risk contribution
- source session when applicable
- plain-language reason
- supporting evidence and structured metadata

## Built-in rules

- SA-R001 Agent added time without downstream review
- SA-R002 Supervisor added time beyond prior version
- SA-R003 Manager added time beyond prior version
- SA-R004 Payroll added time beyond prior version
- SA-R005 System activity removed from manual version
- SA-R006 Phone activity removed from manual version
- SA-R007 Manual activity inserted
- SA-R008 Manual activity type changed
- SA-R009 Large contiguous manual addition
- SA-R010 Rounded manual time addition
- SA-R011 Final manual duration exceeds captured evidence
- SA-R012 Supervisor edited without Agent version
- SA-R013 Manager edited without Agent/Supervisor version
- SA-R014 Payroll modification after manager action
- SA-R015 Overlapping login sessions
- SA-R016 Repeated modified sessions on same employee-day
- SA-R017 Quartz multiple-login/abnormal-shutdown flag
- SA-R018 Manually added session without Phone/System corroboration
- SA-R019 Low captured evidence coverage
- SA-R020 Excessive final payable duration
- SA-R021 Manual version reduced recorded inactivity
- SA-R022 Manual time addition lacks activity comment
- SA-R023 Phone/System captured-time mismatch
- SA-R024 Multiple manual workflow stages modified session

## Risk levels

- 0-20 Normal
- 21-40 Review
- 41-60 Suspicious
- 61-80 High
- 81-100 Critical

Risk is not a declaration of fraud. It is an investigation-prioritization score derived from deterministic evidence.

## API

`GET /api/v1/assessments/{agent_id}/{shift_date}?ingestion_run_id=<uuid>`

The endpoint reconstructs the immutable employee-day timeline, runs activity matching, executes the deterministic rules, and returns the risk assessment.
