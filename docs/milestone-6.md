# Milestone 6 - Organizational Behavioral Intelligence and Collusion Detection

Adds optional as-of-shift organizational dimensions (`manager_id`, `site_id`, `site_name`, `team_id`), supervisor-agent and manager-agent repeated intervention signals, intervention concentration, payroll adjustment concentration by supervisor team, and campaign/site peer outliers.

## Quartz API enrichment
The login-session API may now optionally provide: `manager_id`, `site_id`, `site_name`, `team_id`. These should represent the hierarchy applicable to the session's shift date, not merely the employee's current hierarchy.

## Limitations
Quartz activities do not currently carry a trustworthy payroll actor identity. Sentinel therefore detects payroll concentration but does not attribute payroll behavior to a named payroll user. Manager analytics are skipped when manager hierarchy is absent.

## Synchronous safety
The initial API caps organizational analysis at 91 shift dates and 500 employee-days. Larger scans must move to the background scan pipeline in a later milestone.
