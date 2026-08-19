# MailTracko

Cold email outreach platform — campaigns, deliverability, and analytics.

## Overview

MailTracko helps users connect email accounts, manage contacts, create campaigns, monitor deliverability, and track performance. Built for individuals, teams, and agencies.

## Stack

Python 3.13 / FastAPI / SQLAlchemy async / PostgreSQL 16 / Redis / Dramatiq

## Architecture

Modular monolith with DDD — each module follows `application → domain → infrastructure → presentation` layers.

```
src/
├── core/          # Config, settings, lifespan, response utils
├── modules/       # identity, campaign, contact, template, inbox, etc.
│   └── {module}/
│       ├── application/   # Use cases, listeners, tasks
│       ├── domain/        # Entities, services, repositories (interfaces)
│       ├── infrastructure/ # Models, repository implementations
│       └── presentation/  # Routers, schemas
├── shared/        # BaseEntity, BaseRepository, UoW, exceptions, notification
└── templates/     # Jinja2 email templates
```

## Quick start

```bash
make setup                    # Install dependencies
docker compose -f docker/docker-compose.base.yml up -d  # Start DB + Redis
make run                      # Start dev server at :8000
make migrate                  # Run migrations
make worker                   # Start background worker
```

## Commands

| Command | Purpose |
|---|---|
| `make lint` | Ruff lint + fix |
| `make test` | Run tests |
| `make migration msg="..."` | Create migration |
| `make create-module` | Scaffold a new module |
| `make localup` | Start all Docker services |
