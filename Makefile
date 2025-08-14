.PHONY: help install run test clean db-init db-upgrade seed-logs docker-build docker-up docker-down

help: ## Show this help message
	@echo "Marx-Tec VM Dashboard - Available Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install Python dependencies
	pip install -r requirements.txt

run: ## Run the Flask development server
	python app.py

test: ## Run tests
	@echo "Testing logging system..."
	@python test_logging.py
	@echo "Testing permission system..."
	@python test_permissions.py

clean: ## Clean up temporary files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.log" -delete

db-init: ## Initialize the database
	python scripts/db_init.py

db-upgrade: ## Run database migrations (placeholder)
	@echo "Database migrations not yet implemented"

seed-logs: ## Send test logs to the system
	@echo "Usage: python scripts/send_fake_logs.py --agent-key YOUR_KEY [--count N] [--server-id SERVER]"

docker-build: ## Build Docker image
	docker build -t marx-tec-dashboard .

docker-up: ## Start services with Docker Compose
	docker-compose up -d

docker-down: ## Stop Docker Compose services
	docker-compose down

docker-logs: ## View Docker Compose logs
	docker-compose logs -f

setup: install db-init ## Complete setup: install dependencies and initialize database
	@echo "Setup complete! Next steps:"
	@echo "1. Set AGENT_KEY in secrets/secret.env"
	@echo "2. Run 'make run' to start the server"
	@echo "3. Test with 'make seed-logs'"

dev: install ## Development setup
	@echo "Development environment ready!"
	@echo "Run 'make run' to start the server"
