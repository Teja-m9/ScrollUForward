#!/usr/bin/env bash
# ScrollUForward Microservices — quick start
# Usage:
#   ./start.sh          → build + start all services
#   ./start.sh dev      → start in dev mode (no rebuild)
#   ./start.sh stop     → stop all services
#   ./start.sh logs     → tail logs for all services
#   ./start.sh status   → show running containers

set -e

COMPOSE="docker compose -f $(dirname "$0")/docker-compose.yml"

case "${1:-}" in
  stop)
    echo "[ScrollU] Stopping all services..."
    $COMPOSE down
    ;;
  logs)
    $COMPOSE logs -f --tail=50
    ;;
  status)
    $COMPOSE ps
    ;;
  dev)
    echo "[ScrollU] Starting services (no rebuild)..."
    $COMPOSE up -d
    $COMPOSE ps
    echo ""
    echo "  Gateway:    http://localhost:8000"
    echo "  Auth:       http://localhost:8001"
    echo "  Content:    http://localhost:8002"
    echo "  Discussion: http://localhost:8003"
    echo "  User:       http://localhost:8004"
    echo "  Chat:       http://localhost:8005"
    echo "  AI Worker:  http://localhost:8006"
    echo "  Redis:      localhost:6379"
    ;;
  *)
    echo "[ScrollU] Building + starting all services..."
    $COMPOSE up -d --build
    $COMPOSE ps
    echo ""
    echo "  API Gateway:  http://localhost:8000"
    echo "  Health check: http://localhost:8000/health"
    echo "  Docs:         http://localhost:8000/docs (gateway)"
    ;;
esac
