#!/bin/bash

# Atlas Travel Advisor - CLI Helper Script
# Usage: ./atlas.sh <command>

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_header() {
    echo -e "${BLUE}🌍 Atlas Travel Advisor${NC}"
    echo "================================"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if Docker is available
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    if ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not available"
        exit 1
    fi
}

# Show help
show_help() {
    print_header
    echo ""
    echo "Available Commands:"
    echo ""
    echo "🚀 Development:"
    echo "  ./atlas.sh start      - Start all services with Docker Compose"
    echo "  ./atlas.sh stop       - Stop all running services"
    echo "  ./atlas.sh build      - Build all Docker images"
    echo "  ./atlas.sh restart    - Restart all services"
    echo ""
    echo "🧪 Testing:"
    echo "  ./atlas.sh test       - Run the complete test suite"
    echo "  ./atlas.sh test-unit  - Run unit tests only"
    echo "  ./atlas.sh test-int   - Run integration tests only"
    echo ""
    echo "📊 Evaluation:"
    echo "  ./atlas.sh eval       - Run AI evaluation scenarios"
    echo ""
    echo "🔧 Utilities:"
    echo "  ./atlas.sh logs       - Show logs from all services"
    echo "  ./atlas.sh shell      - Open shell in backend container"
    echo "  ./atlas.sh clean      - Clean up containers and volumes"
    echo "  ./atlas.sh health     - Check service health"
    echo ""
    echo "📚 Database:"
    echo "  ./atlas.sh db-upgrade - Run database migrations"
    echo "  ./atlas.sh db-reset   - Reset database (destroys data)"
    echo ""
    echo "🌐 Quick Access URLs:"
    echo "  Frontend: http://localhost:8501"
    echo "  Backend API: http://localhost:8000"
    echo "  API Docs: http://localhost:8000/docs"
}

# Start services
start_services() {
    print_info "Starting Atlas Travel Advisor services..."
    check_docker
    docker compose up -d
    print_success "Services started!"
    echo ""
    print_info "Access URLs:"
    echo "  Frontend: http://localhost:8501"
    echo "  Backend: http://localhost:8000"
    echo "  API Docs: http://localhost:8000/docs"
}

# Stop services
stop_services() {
    print_info "Stopping all services..."
    check_docker
    docker compose down
    print_success "Services stopped!"
}

# Build images
build_images() {
    print_info "Building all Docker images..."
    check_docker
    docker compose build
    print_success "Build complete!"
}

# Restart services
restart_services() {
    print_info "Restarting services..."
    stop_services
    start_services
}

# Run tests
run_tests() {
    print_info "Running complete test suite..."
    check_docker
    
    print_info "Running unit tests..."
    docker compose exec backend python -m pytest tests/unit/ -v
    
    print_info "Running integration tests..."
    docker compose exec backend python -m pytest tests/integration/ -v
    
    print_success "All tests complete!"
}

# Run unit tests only
run_unit_tests() {
    print_info "Running unit tests..."
    check_docker
    docker compose exec backend python -m pytest tests/unit/ -v
}

# Run integration tests only
run_integration_tests() {
    print_info "Running integration tests..."
    check_docker
    docker compose exec backend python -m pytest tests/integration/ -v
}

# Run evaluation
run_evaluation() {
    print_info "Running AI evaluation scenarios..."
    check_docker
    docker compose exec backend python eval/run_scenarios.py
    print_success "Evaluation complete!"
}

# Show logs
show_logs() {
    check_docker
    docker compose logs -f
}

# Open shell
open_shell() {
    print_info "Opening shell in backend container..."
    check_docker
    docker compose exec backend /bin/bash
}

# Clean up
clean_up() {
    print_warning "Cleaning up containers and volumes..."
    check_docker
    docker compose down -v --remove-orphans
    docker system prune -f
    print_success "Cleanup complete!"
}

# Health check
health_check() {
    print_info "Checking service health..."
    
    # Check backend
    if curl -s http://localhost:8000/api/v1/ops/healthz > /dev/null 2>&1; then
        print_success "Backend is healthy"
    else
        print_error "Backend not responding"
    fi
    
    # Check frontend
    if curl -s http://localhost:8501 > /dev/null 2>&1; then
        print_success "Frontend is healthy"
    else
        print_error "Frontend not responding"
    fi
}

# Database operations
db_upgrade() {
    print_info "Upgrading database to latest migration..."
    check_docker
    docker compose exec backend alembic upgrade head
    print_success "Database upgrade complete!"
}

db_reset() {
    print_warning "WARNING: This will destroy all data!"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Resetting database..."
        docker compose down -v
        docker compose up -d db redis
        sleep 5
        docker compose exec backend alembic upgrade head
        print_success "Database reset complete!"
    else
        print_info "Database reset cancelled."
    fi
}

# Main command handler
case "${1:-help}" in
    "start")
        start_services
        ;;
    "stop")
        stop_services
        ;;
    "build")
        build_images
        ;;
    "restart")
        restart_services
        ;;
    "test")
        run_tests
        ;;
    "test-unit")
        run_unit_tests
        ;;
    "test-int")
        run_integration_tests
        ;;
    "eval")
        run_evaluation
        ;;
    "logs")
        show_logs
        ;;
    "shell")
        open_shell
        ;;
    "clean")
        clean_up
        ;;
    "health")
        health_check
        ;;
    "db-upgrade")
        db_upgrade
        ;;
    "db-reset")
        db_reset
        ;;
    "help"|"--help"|"-h")
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac
