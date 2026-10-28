up:
	docker compose up --build -d

down:
	docker compose down

destroy:
	docker compose down -v

logs:
	docker compose logs -f api worker

token:
	docker compose exec api python -m app.cli.dev_token --role admin

test:
	docker compose --profile test run --build --rm test

lint:
	docker compose run --rm api ruff check app tests

migrate:
	docker compose exec api alembic upgrade head

status:
	docker compose ps
