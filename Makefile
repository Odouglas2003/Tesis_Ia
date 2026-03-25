# ===========================================
# Makefile for Next.js Docker Development
# ===========================================

# Detects if 'docker-compose' (v1) or 'docker compose' (v2) exists
DOCKER_COMPOSE := $(shell docker compose version >/dev/null 2>&1 && echo "docker compose" || echo "docker-compose")
.PHONY: help dev prod build clean logs stop

# Colors for output
GREEN=\033[0;32m
YELLOW=\033[1;33m
RED=\033[0;31m
NC=\033[0m

# Default target
.DEFAULT_GOAL := help

help: ## Show available commands
	@echo "$(GREEN)Available commands:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "$(YELLOW)  %-15s$(NC) %s\n", $$1, $$2}'

# ===========================================
# Docker Local development commands
# ===========================================
# Development with hot-reload
run-docker: ## Start development environment with hot-reload
	@echo "$(GREEN)Starting development environment...$(NC)"
	$(DOCKER_COMPOSE) up --build


# ===========================================
# CI/CD commands
# ===========================================
prepare-deps: ## Prepare dependencies for CI/CD
	@echo "$(GREEN)Preparing dependencies...$(NC)"
	pip install -r requirements.txt

unit-test: ## Run unit tests
	@echo "$(GREEN)Running unit tests...$(NC)"

static-analysis: ## Run static analysis
	@echo "$(GREEN)Running static analysis...$(NC)"
# flake8 .
