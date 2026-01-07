# Newport Demo - Container-First Development
# ==========================================
# All development, testing, and execution happens inside containers.
# See CLAUDE.md for full architecture documentation.

COMPOSE = docker compose

.PHONY: dev stop logs test test-cov test-vlm test-ds \
        shell-app shell-vlm shell-ds build-app build-all clean status

# ============================================================================
# DEVELOPMENT - Start/Stop/Logs
# ============================================================================

# Full stack (requires GPU + NGC/dustynv images)
dev:
	$(COMPOSE) up -d
	@echo "Stack started. View status: make status"

# Lightweight dev (app + redis only, no GPU required)
dev-lite:
	$(COMPOSE) -f docker-compose.lite.yml up -d
	@echo "Lite stack started (app + redis). View status: make status-lite"

status-lite:
	$(COMPOSE) -f docker-compose.lite.yml ps

stop-lite:
	$(COMPOSE) -f docker-compose.lite.yml down

logs-lite:
	$(COMPOSE) -f docker-compose.lite.yml logs -f

test-lite:
	$(COMPOSE) -f docker-compose.lite.yml exec app pytest tests/ -v

shell-lite:
	$(COMPOSE) -f docker-compose.lite.yml exec app bash

stop:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f

logs-app:
	$(COMPOSE) logs -f app

logs-vlm:
	$(COMPOSE) logs -f vlm

logs-ds:
	$(COMPOSE) logs -f deepstream

status:
	$(COMPOSE) ps

# ============================================================================
# TESTING - Always inside containers
# ============================================================================

test:
	$(COMPOSE) exec app pytest tests/ -v

test-cov:
	$(COMPOSE) exec app pytest tests/ -v --cov=src --cov-report=term-missing

test-vlm:
	$(COMPOSE) exec vlm python -m pytest /app/src/tests/ -v

test-ds:
	$(COMPOSE) exec deepstream python -m pytest /app/src/tests/ -v

test-all: test test-vlm test-ds

# ============================================================================
# INTERACTIVE - Shell access for debugging
# ============================================================================

shell-app:
	$(COMPOSE) exec app bash

shell-vlm:
	$(COMPOSE) exec vlm bash

shell-ds:
	$(COMPOSE) exec deepstream bash

redis-cli:
	$(COMPOSE) exec redis redis-cli

# ============================================================================
# BUILDING - Rebuild containers after changes
# ============================================================================

build-app:
	$(COMPOSE) build app

build-all:
	$(COMPOSE) build

rebuild-app: build-app
	$(COMPOSE) up -d app

# ============================================================================
# UTILITIES
# ============================================================================

restart-%:
	$(COMPOSE) restart $*

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

# ============================================================================
# HELP
# ============================================================================

help:
	@echo "Newport Demo - Container-First Development"
	@echo ""
	@echo "  make dev          Start all containers"
	@echo "  make stop         Stop all containers"
	@echo "  make status       Show container status"
	@echo "  make logs         Follow all logs"
	@echo "  make logs-app     Follow app logs"
	@echo ""
	@echo "  make test         Run app tests (in container)"
	@echo "  make test-cov     Run tests with coverage"
	@echo "  make test-all     Run all container tests"
	@echo ""
	@echo "  make shell-app    Shell into app container"
	@echo "  make shell-vlm    Shell into VLM container"
	@echo "  make redis-cli    Redis CLI"
	@echo ""
	@echo "  make build-app    Rebuild app container"
	@echo "  make build-all    Rebuild all containers"
	@echo ""
	@echo "See CLAUDE.md for full documentation."
