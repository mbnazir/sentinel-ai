# Quartz Yii 1.1 reference adapter

`SentinelController.php` is a reference implementation for the two read-only APIs Sentinel expects.

Before using it:
- adapt controller/routing conventions to Quartz;
- use the organization's API authentication mechanism if available;
- restrict network access to the Sentinel service;
- use a read-only service identity;
- confirm timestamp timezone handling;
- performance-test on a non-production environment;
- do not add manager/site/team hierarchy unless it is authoritative for the historical shift date.

Suggested routes:

`GET /api/sentinel/v1/login-sessions`

`GET /api/sentinel/v1/activities`
