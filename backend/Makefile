PROJECT_NAME ?= mail-tracko
TEST_PROJECT_NAME ?= $(PROJECT_NAME)-test
TEST_COMPOSE_FILE ?= docker/docker-compose-test.yml

setup:
	@echo "Setting up the project..."
	python -m scripts.setup.project_setup

lint:
	@echo "Running linter..."
	uv run ruff check --fix .

run:
	@echo "Running application..."
	python -m src.main

entity:
	@echo "Creating a new entity"
	python scripts/entity/generate_entity.py

test:
	@echo "Starting isolated test database..."
	@set -e; \
	docker compose -p $(TEST_PROJECT_NAME) -f $(TEST_COMPOSE_FILE) up -d; \
	trap 'docker compose -p $(TEST_PROJECT_NAME) -f $(TEST_COMPOSE_FILE) down -v' EXIT; \
	until docker compose -p $(TEST_PROJECT_NAME) -f $(TEST_COMPOSE_FILE) exec -T db_test pg_isready -U postgres -d mailtracko_db_test >/dev/null 2>&1; do \
		echo "Waiting for test database to be ready..."; \
		sleep 2; \
	done; \
	echo "Running tests..."; \
	PYTHONPATH=. ENVIRONMENT=testing uv run pytest -v -s tests/

migration:
	@echo "Creating migration..."
	MIGRATION_NAME=$(name) alembic revision -m "$(msg)"

migrate:
	@echo "Migrating the migrations to the database..."
	alembic upgrade head

downgrade:
	@echo "Migrating the migrations to the database..."
	alembic downgrade -1

localup:
	@echo "Starting the application with Docker Compose..."
	PROJECT_NAME=$(PROJECT_NAME) docker compose -p $(PROJECT_NAME)-local -f docker/docker-compose.base.yml -f docker/docker-compose.local.yml up -d

localb:
	@echo "Starting the application with Docker Compose in build mode..."
	PROJECT_NAME=$(PROJECT_NAME) docker compose -p $(PROJECT_NAME)-local -f docker/docker-compose.base.yml -f docker/docker-compose.local.yml build


localdown:
	@echo "Stopping the application with Docker Compose..."
	docker compose -p $(PROJECT_NAME)-local -f docker/docker-compose.base.yml -f docker/docker-compose.local.yml down

localdownv:
	@echo "Stopping the application with Docker Compose..."
	docker compose -p $(PROJECT_NAME)-local -f docker/docker-compose.base.yml -f docker/docker-compose.local.yml down -v

devup:
	@echo "Starting the application in development mode with Docker Compose..."
	PROJECT_NAME=$(PROJECT_NAME) docker compose -p $(PROJECT_NAME)-dev -f docker/docker-compose.base.yml -f docker/docker-compose.development.yml up -d --force-recreate --remove-orphans

devb:
	@echo "Starting the application in development mode with Docker Compose in build mode..."
	PROJECT_NAME=$(PROJECT_NAME) docker compose -p $(PROJECT_NAME)-dev -f docker/docker-compose.base.yml -f docker/docker-compose.development.yml build --no-cache --pull 

devdown:
	@echo "Stopping the application in development mode with Docker Compose..."
	docker compose -p $(PROJECT_NAME)-dev -f docker/docker-compose.base.yml -f docker/docker-compose.development.yml down

devdownv:
	@echo "Stopping the application in development mode with Docker Compose..."
	docker compose -p $(PROJECT_NAME)-dev -f docker/docker-compose.base.yml -f docker/docker-compose.development.yml down -v

stagingup:
	@echo "Starting the application in staging mode with Docker Compose..."
	PROJECT_NAME=$(PROJECT_NAME) docker compose -p $(PROJECT_NAME)-staging -f docker/docker-compose.base.yml -f docker/docker-compose.staging.yml up -d --remove-orphans

stagingb:
	@echo "Starting the application in staging mode with Docker Compose in build mode..."
	PROJECT_NAME=$(PROJECT_NAME) docker compose -p $(PROJECT_NAME)-staging -f docker/docker-compose.base.yml -f docker/docker-compose.staging.yml build

stagingdown:
	@echo "Stopping the application in staging mode with Docker Compose..."
	docker compose -p $(PROJECT_NAME)-staging -f docker/docker-compose.base.yml -f docker/docker-compose.staging.yml down

stagingdownv:
	@echo "Stopping the application in staging mode with Docker Compose..."
	docker compose -p $(PROJECT_NAME)-staging -f docker/docker-compose.base.yml -f docker/docker-compose.staging.yml down -v


background_task:
	@echo "Starting background task worker..."
	OUTBOX_POLLER_AUTOSTART=true dramatiq src.shared.infrastructure.tasks.registry

list_handlers:
	@echo "Listing all registered mediator handlers..."
	python -m scripts.mediators.list_handlers

create-feature:
	@echo "Creating a new feature"
	@read -p "Enter feature name: " feature_name; \
	feature_dir="src/modules/$$feature_name"; \
	mkdir -p $$feature_dir && \
	touch "$$feature_dir/__init__.py" && \
	subfolders="application domain infrastructure presentation"; \
	for folder in $$subfolders; do \
		mkdir -p "$$feature_dir/$$folder" && \
		touch "$$feature_dir/$$folder/__init__.py"; \
	done; \
	echo "Feature '$$feature_name' structure  created successfully!"
