# Executive Analytics Dashboard

Milestone 14 adds leadership-facing analytics.

## Backend

Endpoint:

```text
GET /api/v1/dashboard/executive
```

Returns:

- total cases
- open cases
- critical cases
- high-risk cases
- average risk score
- risk distribution
- monthly trend
- top risk entities

## Frontend

Adds:

- KPI cards
- risk distribution chart
- case volume and risk trend chart
- top risk entities table

## Purpose

This view is for executives and compliance leadership. It shows the integrity risk operating picture instead of individual case detail.
