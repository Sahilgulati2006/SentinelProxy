.PHONY: setup install redis backend frontend bootstrap health ready dev-check stop-redis lint clean docker-up docker-down docker-bootstrap docker-logs

PYTHON := python3.12
VENV := .venv
PIP := $(VENV)/bin/pip
PY := $(VENV)/bin/python
UVICORN := $(VENV)/bin/uvicorn

setup:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

install:
	$(PIP) install -r requirements.txt

redis:
	docker compose up -d redis

stop-redis:
	docker compose stop redis

backend:
	$(UVICORN) app.main:app --reload

frontend:
	cd apps/web && npm run dev

bootstrap:
	$(PY) -m scripts.bootstrap_dev

health:
	curl http://127.0.0.1:8000/health

ready:
	curl http://127.0.0.1:8000/ready

dev-check:
	@echo "Checking backend health..."
	curl -s http://127.0.0.1:8000/health
	@echo "\nChecking readiness..."
	curl -s http://127.0.0.1:8000/ready
	@echo ""

clean:
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache

docker-up:
	docker compose up --build

docker-down:
	docker compose down

docker-bootstrap:
	docker exec -it sentinelproxy-backend python -m scripts.bootstrap_dev

docker-logs:
	docker compose logs -f

lint:
	cd apps/web && npm run lint