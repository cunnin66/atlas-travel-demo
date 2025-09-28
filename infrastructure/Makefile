# Atlas Travel Advisor - CLI Shortcuts
# Usage: make <command>

.PHONY: help start stop build test eval clean logs shell-backend shell-frontend

# Default target
help:
	@echo "Atlas Travel Advisor - Available Commands:"
	@echo ""
	@echo "🚀 Development:"
	@echo "  make start      - Start all services with Docker Compose"
	@echo "  make stop       - Stop all running services"
	@echo "  make build      - Build all Docker images"
	@echo "  make restart    - Restart all services (stop + start)"
	@echo ""
	@echo "🧪 Testing:"
	@echo "  make test       - Run the complete test suite"
	@echo "  make test-unit  - Run unit tests only"
	@echo "  make test-int   - Run integration tests only"
	@echo ""
	@echo "📊 Evaluation:"
	@echo "  make eval       - Run AI evaluation scenarios"
	@echo ""
	@echo "🔧 Utilities:"
	@echo "  make logs       - Show logs from all services"
	@echo "  make logs-backend - Show backend logs only"
	@echo "  make logs-frontend - Show frontend logs only"
	@echo "  make shell-backend - Open shell in backend container"
	@echo "  make shell-frontend - Open shell in frontend container"
	@echo "  make clean      - Clean up containers and volumes"
	@echo ""
	@echo "📚 Database:"
	@echo "  make db-migrate - Run database migrations"
	@echo "  make db-upgrade - Upgrade database to latest migration"
	@echo "  make db-reset   - Reset database (WARNING: destroys data)"
	@echo ""
	@echo "🌐 Quick Access:"
	@echo "  Frontend: http://localhost:8501"
	@echo "  Backend API: http://localhost:8000"
	@echo "  API Docs: http://localhost:8000/docs"

# Development Commands
start:
	@echo "🚀 Starting Atlas Travel Advisor services..."
	docker compose up -d
	@echo "✅ Services started!"
	@echo "   Frontend: http://localhost:8501"
	@echo "   Backend: http://localhost:8000"
	@echo "   API Docs: http://localhost:8000/docs"

stop:
	@echo "🛑 Stopping all services..."
	docker compose down
	@echo "✅ Services stopped!"

build:
	@echo "🔨 Building all Docker images..."
	docker compose build
	@echo "✅ Build complete!"

restart: stop start

# Testing Commands
test:
	@echo "🧪 Running complete test suite..."
	@echo "📋 Running unit tests..."
	docker compose exec backend python -m pytest tests/unit/ -v
	@echo "📋 Running integration tests..."
	docker compose exec backend python -m pytest tests/integration/ -v
	@echo "✅ All tests complete!"

test-unit:
	@echo "🧪 Running unit tests..."
	docker compose exec backend python -m pytest tests/unit/ -v

test-int:
	@echo "🧪 Running integration tests..."
	docker compose exec backend python -m pytest tests/integration/ -v

# Evaluation Commands
eval:
	@echo "📊 Running AI evaluation scenarios..."
	docker compose exec backend python eval/run_scenarios.py
	@echo "✅ Evaluation complete!"

# Utility Commands
logs:
	docker compose logs -f

logs-backend:
	docker compose logs -f backend

logs-frontend:
	docker compose logs -f frontend

shell-backend:
	docker compose exec backend /bin/bash

shell-frontend:
	docker compose exec frontend /bin/bash

clean:
	@echo "🧹 Cleaning up containers and volumes..."
	docker compose down -v --remove-orphans
	docker system prune -f
	@echo "✅ Cleanup complete!"

# Database Commands
db-migrate:
	@echo "📊 Generating database migration..."
	docker compose exec backend alembic revision --autogenerate -m "Auto migration"

db-upgrade:
	@echo "📊 Upgrading database to latest migration..."
	docker compose exec backend alembic upgrade head

db-reset:
	@echo "⚠️  WARNING: This will destroy all data!"
	@read -p "Are you sure? (y/N): " confirm && [ "$$confirm" = "y" ]
	docker compose down -v
	docker compose up -d db redis
	sleep 5
	docker compose exec backend alembic upgrade head
	@echo "✅ Database reset complete!"

# Development helpers
dev-setup:
	@echo "🔧 Setting up development environment..."
	cp .env.example .env
	@echo "📝 Please edit .env file with your configuration"
	@echo "✅ Development setup complete!"

# Health check
health:
	@echo "🏥 Checking service health..."
	@curl -s http://localhost:8000/api/v1/ops/healthz || echo "❌ Backend not responding"
	@curl -s http://localhost:8501 > /dev/null && echo "✅ Frontend is healthy" || echo "❌ Frontend not responding"

# Install dependencies (for local development)
install-backend:
	cd backend && pip install -r requirements.txt

install-frontend:
	cd frontend && pip install -r requirements.txt

install: install-backend install-frontend
