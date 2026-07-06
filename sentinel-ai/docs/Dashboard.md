# React Investigation Dashboard

Milestone 11 introduces the first user-facing product surface.

## Screens

- investigation queue
- investigation detail
- evidence viewer
- comments viewer
- AI narrative viewer
- summary cards

## API behavior

The dashboard calls:

```text
/api/v1/workflow/investigations
/api/v1/workflow/investigations/{case_id}/narrative
```

If the backend is unavailable or has no cases, the dashboard falls back to demo data.

## Run locally

```bash
cd frontend
npm install
npm run dev
```

or through Docker Compose:

```bash
docker compose up --build
```

## Next improvements

- real authentication
- role-based views
- timeline visualization
- evidence deep links
- assignment/transition/comment actions wired to UI
- charts for behavior analytics
