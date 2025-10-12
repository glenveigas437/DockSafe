# DockSafe Makefile
# Easy commands for development and deployment

.PHONY: help build test deploy clean dev prod

# Default target
help:
	@echo "DockSafe - Container Vulnerability Scanner"
	@echo "=========================================="
	@echo ""
	@echo "Available commands:"
	@echo "  make dev          - Start development environment"
	@echo "  make prod         - Start production environment"
	@echo "  make build        - Build Docker images"
	@echo "  make test         - Run tests"
	@echo "  make lint         - Run linting"
	@echo "  make deploy       - Deploy to production"
	@echo "  make clean        - Clean up containers and images"
	@echo "  make logs         - View application logs"
	@echo "  make shell        - Open shell in app container"
	@echo "  make migrate      - Run database migrations"
	@echo "  make backup       - Backup database"
	@echo "  make restore      - Restore database"
	@echo "  make terraform    - Deploy infrastructure with Terraform"
	@echo "  make ansible      - Deploy with Ansible"
	@echo "  make k8s          - Deploy to Kubernetes"
	@echo ""

# Development
dev:
	@echo "🚀 Starting development environment..."
	docker-compose up -d
	@echo "✅ Development environment started!"
	@echo "📱 Application: http://localhost:5000"
	@echo "📊 Prometheus: http://localhost:9090"
	@echo "📈 Grafana: http://localhost:3000"

# Production
prod:
	@echo "🚀 Starting production environment..."
	docker-compose -f docker-compose.prod.yml up -d
	@echo "✅ Production environment started!"
	@echo "📱 Application: http://localhost"

# Build
build:
	@echo "🔨 Building Docker images..."
	docker build -t docksafe:latest .
	docker build -f Dockerfile.dev -t docksafe:dev .
	@echo "✅ Images built successfully!"

# Test
test:
	@echo "🧪 Running tests..."
	docker-compose exec docksafe-app pytest --cov=app --cov-report=html
	@echo "✅ Tests completed!"

# Lint
lint:
	@echo "🔍 Running linting..."
	docker-compose exec docksafe-app flake8 app/
	docker-compose exec docksafe-app black --check app/
	@echo "✅ Linting completed!"

# Deploy
deploy:
	@echo "🚀 Deploying to production..."
	./scripts/deploy.sh latest production docker-compose
	@echo "✅ Deployment completed!"

# Clean
clean:
	@echo "🧹 Cleaning up..."
	docker-compose down -v
	docker-compose -f docker-compose.prod.yml down -v
	docker system prune -f
	docker volume prune -f
	@echo "✅ Cleanup completed!"

# Logs
logs:
	@echo "📋 Viewing application logs..."
	docker-compose logs -f docksafe-app

# Shell
shell:
	@echo "🐚 Opening shell in app container..."
	docker-compose exec docksafe-app bash

# Database
migrate:
	@echo "🗄️ Running database migrations..."
	docker-compose exec docksafe-app flask db upgrade
	@echo "✅ Migrations completed!"

backup:
	@echo "💾 Backing up database..."
	docker-compose exec postgres pg_dump -U docksafe docksafe > backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "✅ Backup completed!"

restore:
	@echo "🔄 Restoring database..."
	@read -p "Enter backup file name: " file; \
	docker-compose exec -T postgres psql -U docksafe -d docksafe < $$file
	@echo "✅ Restore completed!"

# Infrastructure
terraform:
	@echo "🏗️ Deploying infrastructure with Terraform..."
	cd terraform && terraform init && terraform plan && terraform apply
	@echo "✅ Infrastructure deployed!"

terraform-destroy:
	@echo "💥 Destroying infrastructure..."
	cd terraform && terraform destroy
	@echo "✅ Infrastructure destroyed!"

ansible:
	@echo "🎭 Deploying with Ansible..."
	cd ansible && ansible-playbook -i inventory.ini deploy.yml
	@echo "✅ Ansible deployment completed!"

k8s:
	@echo "☸️ Deploying to Kubernetes..."
	kubectl apply -f k8s/docksafe.yaml
	kubectl rollout status deployment/docksafe-app -n docksafe
	@echo "✅ Kubernetes deployment completed!"

k8s-delete:
	@echo "🗑️ Deleting Kubernetes resources..."
	kubectl delete -f k8s/docksafe.yaml
	@echo "✅ Kubernetes resources deleted!"

# Security
security-scan:
	@echo "🔒 Running security scan..."
	trivy image docksafe:latest
	@echo "✅ Security scan completed!"

# Monitoring
monitoring:
	@echo "📊 Starting monitoring stack..."
	docker-compose up -d prometheus grafana
	@echo "✅ Monitoring started!"
	@echo "📊 Prometheus: http://localhost:9090"
	@echo "📈 Grafana: http://localhost:3000"

# Health check
health:
	@echo "🏥 Checking application health..."
	curl -f http://localhost/health || echo "❌ Health check failed!"

# Setup
setup:
	@echo "⚙️ Setting up development environment..."
	cp .env.example .env
	@echo "📝 Please edit .env file with your configuration"
	@echo "🔑 Generate Google OAuth credentials"
	@echo "📧 Configure email settings"
	@echo "✅ Setup completed!"

# Update
update:
	@echo "🔄 Updating application..."
	git pull origin main
	docker-compose pull
	docker-compose up -d
	@echo "✅ Update completed!"

# Status
status:
	@echo "📊 Application Status:"
	@echo "===================="
	docker-compose ps
	@echo ""
	@echo "📊 Resource Usage:"
	@echo "================="
	docker stats --no-stream

# Install dependencies
install:
	@echo "📦 Installing dependencies..."
	pip install -r requirements.txt
	npm install
	@echo "✅ Dependencies installed!"

# Format code
format:
	@echo "🎨 Formatting code..."
	black app/
	@echo "✅ Code formatted!"

# Type check
type-check:
	@echo "🔍 Running type checks..."
	mypy app/
	@echo "✅ Type checks completed!"

# Coverage
coverage:
	@echo "📊 Generating coverage report..."
	pytest --cov=app --cov-report=html --cov-report=term
	@echo "✅ Coverage report generated!"
	@echo "📄 Open htmlcov/index.html to view detailed report"

# Performance test
perf-test:
	@echo "⚡ Running performance tests..."
	locust -f tests/performance/locustfile.py --host=http://localhost
	@echo "✅ Performance tests completed!"

# Documentation
docs:
	@echo "📚 Generating documentation..."
	sphinx-build -b html docs/ docs/_build/
	@echo "✅ Documentation generated!"
	@echo "📄 Open docs/_build/index.html to view documentation"

# Release
release:
	@echo "🚀 Creating release..."
	@read -p "Enter version number: " version; \
	git tag -a v$$version -m "Release v$$version"; \
	git push origin v$$version
	@echo "✅ Release v$$version created!"

# All-in-one development setup
dev-setup: setup install build dev migrate
	@echo "🎉 Development environment ready!"
	@echo "📱 Application: http://localhost:5000"
	@echo "📊 Prometheus: http://localhost:9090"
	@echo "📈 Grafana: http://localhost:3000"
