# Development Guide

## Start environment

```bash
cp .env.example .env
docker compose up --build
```

## Run migrations

```bash
cd backend
alembic upgrade head
```

## Run tests

```bash
cd backend
pytest
```
