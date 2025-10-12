#!/bin/bash

# DockSafe Deployment Script
# This script handles the complete deployment of DockSafe application

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="docksafe"
DOCKER_REGISTRY="ghcr.io"
IMAGE_TAG="${1:-latest}"
ENVIRONMENT="${2:-production}"
DEPLOYMENT_METHOD="${3:-docker-compose}"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_requirements() {
    log_info "Checking deployment requirements..."
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check if required files exist
    if [ ! -f "docker-compose.prod.yml" ]; then
        log_error "docker-compose.prod.yml not found!"
        exit 1
    fi
    
    if [ ! -f ".env" ]; then
        log_warning ".env file not found. Creating from template..."
        create_env_file
    fi
    
    log_success "All requirements met!"
}

create_env_file() {
    cat > .env << EOF
# DockSafe Environment Configuration
FLASK_ENV=production
SECRET_KEY=your-secret-key-change-this
DATABASE_URL=postgresql://docksafe:password@postgres:5432/docksafe
REDIS_URL=redis://redis:6379/0

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Email Configuration
DOCSAFE_EMAIL_SMTP_SERVER=smtp.gmail.com
DOCSAFE_EMAIL_SMTP_PORT=587
DOCSAFE_EMAIL_USERNAME=noreply.docksafe@gmail.com
DOCSAFE_EMAIL_PASSWORD=your-app-password
DOCSAFE_EMAIL_FROM=noreply.docksafe@gmail.com
DOCSAFE_EMAIL_USE_TLS=true
EOF
    log_warning "Please update the .env file with your actual configuration values!"
}

build_image() {
    log_info "Building Docker image..."
    docker build -t ${DOCKER_REGISTRY}/${APP_NAME}:${IMAGE_TAG} .
    log_success "Docker image built successfully!"
}

push_image() {
    log_info "Pushing Docker image to registry..."
    docker push ${DOCKER_REGISTRY}/${APP_NAME}:${IMAGE_TAG}
    log_success "Docker image pushed successfully!"
}

deploy_docker_compose() {
    log_info "Deploying with Docker Compose..."
    
    # Stop existing containers
    docker-compose -f docker-compose.prod.yml down
    
    # Pull latest images
    docker-compose -f docker-compose.prod.yml pull
    
    # Start services
    docker-compose -f docker-compose.prod.yml up -d
    
    # Wait for services to be ready
    log_info "Waiting for services to be ready..."
    sleep 30
    
    # Check if application is running
    if curl -f http://localhost/health > /dev/null 2>&1; then
        log_success "Application is running and healthy!"
    else
        log_error "Application health check failed!"
        exit 1
    fi
}

deploy_kubernetes() {
    log_info "Deploying to Kubernetes..."
    
    # Check if kubectl is available
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed. Please install kubectl first."
        exit 1
    fi
    
    # Apply Kubernetes manifests
    kubectl apply -f k8s/docksafe.yaml
    
    # Wait for deployment to be ready
    kubectl rollout status deployment/docksafe-app -n docksafe
    
    log_success "Kubernetes deployment completed!"
}

run_tests() {
    log_info "Running deployment tests..."
    
    # Test database connection
    if docker-compose -f docker-compose.prod.yml exec -T postgres pg_isready -U docksafe; then
        log_success "Database connection test passed!"
    else
        log_error "Database connection test failed!"
        exit 1
    fi
    
    # Test Redis connection
    if docker-compose -f docker-compose.prod.yml exec -T redis redis-cli ping | grep -q PONG; then
        log_success "Redis connection test passed!"
    else
        log_error "Redis connection test failed!"
        exit 1
    fi
    
    # Test application health
    if curl -f http://localhost/health > /dev/null 2>&1; then
        log_success "Application health test passed!"
    else
        log_error "Application health test failed!"
        exit 1
    fi
}

setup_monitoring() {
    log_info "Setting up monitoring..."
    
    # Start Prometheus and Grafana if not already running
    if ! docker-compose -f docker-compose.prod.yml ps prometheus | grep -q Up; then
        docker-compose -f docker-compose.prod.yml up -d prometheus grafana
        log_success "Monitoring services started!"
    else
        log_info "Monitoring services already running!"
    fi
}

cleanup() {
    log_info "Cleaning up old images..."
    docker image prune -f
    log_success "Cleanup completed!"
}

show_status() {
    log_info "Deployment Status:"
    echo "=================="
    docker-compose -f docker-compose.prod.yml ps
    echo ""
    log_info "Application URLs:"
    echo "=================="
    echo "Application: http://localhost"
    echo "Health Check: http://localhost/health"
    echo "Prometheus: http://localhost:9090"
    echo "Grafana: http://localhost:3000 (admin/admin123)"
}

# Main deployment function
main() {
    log_info "Starting DockSafe deployment..."
    log_info "Environment: ${ENVIRONMENT}"
    log_info "Image Tag: ${IMAGE_TAG}"
    log_info "Deployment Method: ${DEPLOYMENT_METHOD}"
    
    check_requirements
    
    case $DEPLOYMENT_METHOD in
        "docker-compose")
            build_image
            deploy_docker_compose
            run_tests
            setup_monitoring
            ;;
        "kubernetes")
            build_image
            push_image
            deploy_kubernetes
            ;;
        *)
            log_error "Invalid deployment method: ${DEPLOYMENT_METHOD}"
            log_info "Valid methods: docker-compose, kubernetes"
            exit 1
            ;;
    esac
    
    cleanup
    show_status
    
    log_success "DockSafe deployment completed successfully!"
}

# Help function
show_help() {
    echo "DockSafe Deployment Script"
    echo "Usage: $0 [IMAGE_TAG] [ENVIRONMENT] [DEPLOYMENT_METHOD]"
    echo ""
    echo "Arguments:"
    echo "  IMAGE_TAG         Docker image tag (default: latest)"
    echo "  ENVIRONMENT       Deployment environment (default: production)"
    echo "  DEPLOYMENT_METHOD Deployment method: docker-compose or kubernetes (default: docker-compose)"
    echo ""
    echo "Examples:"
    echo "  $0                           # Deploy with default settings"
    echo "  $0 v1.0.0                    # Deploy specific version"
    echo "  $0 latest staging            # Deploy to staging environment"
    echo "  $0 v1.0.0 production kubernetes  # Deploy to Kubernetes"
}

# Handle command line arguments
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    show_help
    exit 0
fi

# Run main function
main
