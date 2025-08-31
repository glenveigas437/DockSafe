#!/bin/bash

# DockSafe Setup Script
# This script sets up the DockSafe vulnerability scanner

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
}

# Function to check if Docker Compose is available
check_docker_compose() {
    if ! command_exists docker-compose && ! docker compose version >/dev/null 2>&1; then
        print_error "Docker Compose is not available. Please install Docker Compose and try again."
        exit 1
    fi
}

# Function to check if Trivy is available
check_trivy() {
    if ! command_exists trivy; then
        print_warning "Trivy is not installed. Installing Trivy..."
        install_trivy
    else
        print_success "Trivy is already installed"
    fi
}

# Function to install Trivy
install_trivy() {
    print_status "Installing Trivy..."
    
    # Detect OS
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        if command_exists apt-get; then
            # Ubuntu/Debian
            wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | sudo apt-key add -
            echo deb https://aquasecurity.github.io/trivy-repo/deb $(lsb_release -sc) main | sudo tee -a /etc/apt/sources.list.d/trivy.list
            sudo apt-get update
            sudo apt-get install -y trivy
        elif command_exists yum; then
            # CentOS/RHEL
            sudo yum install -y https://github.com/aquasecurity/trivy/releases/download/v0.48.3/trivy_0.48.3_Linux-64bit.rpm
        else
            print_error "Unsupported Linux distribution. Please install Trivy manually."
            exit 1
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command_exists brew; then
            brew install trivy
        else
            print_error "Homebrew is not installed. Please install Homebrew or Trivy manually."
            exit 1
        fi
    else
        print_error "Unsupported operating system. Please install Trivy manually."
        exit 1
    fi
    
    print_success "Trivy installed successfully"
}

# Function to create environment file
create_env_file() {
    if [ ! -f .env ]; then
        print_status "Creating .env file..."
        cat > .env << EOF
# DockSafe Environment Configuration

# Flask Configuration
FLASK_ENV=development
SECRET_KEY=$(openssl rand -hex 32)

# Database Configuration
DATABASE_URL=postgresql://docksafe:docksafe_password@localhost:5432/docksafe

# Scanner Configuration
SCANNER_TYPE=trivy
SCANNER_TIMEOUT=300
VULNERABILITY_THRESHOLD=HIGH

# Notification Configuration
SLACK_WEBHOOK_URL=
TEAMS_WEBHOOK_URL=
EMAIL_SMTP_SERVER=
EMAIL_SMTP_PORT=587
EMAIL_USERNAME=
EMAIL_PASSWORD=

# Dashboard Configuration
DASHBOARD_REFRESH_INTERVAL=30
MAX_SCAN_HISTORY=1000

# Monitoring Configuration
PROMETHEUS_ENABLED=true
GRAFANA_URL=http://localhost:3000
GRAFANA_API_KEY=

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=docksafe.log
EOF
        print_success ".env file created"
    else
        print_warning ".env file already exists"
    fi
}

# Function to create logs directory
create_logs_directory() {
    if [ ! -d logs ]; then
        print_status "Creating logs directory..."
        mkdir -p logs
        print_success "Logs directory created"
    fi
}

# Function to setup database
setup_database() {
    print_status "Setting up database..."
    
    # Start PostgreSQL container
    docker-compose up -d postgres
    
    # Wait for PostgreSQL to be ready
    print_status "Waiting for PostgreSQL to be ready..."
    sleep 10
    
    # Check if PostgreSQL is ready
    until docker-compose exec -T postgres pg_isready -U docksafe -d docksafe; do
        print_status "Waiting for PostgreSQL..."
        sleep 2
    done
    
    print_success "Database setup completed"
}

# Function to run database migrations
run_migrations() {
    print_status "Running database migrations..."
    
    # Create tables
    docker-compose run --rm docksafe python -c "
from app import create_app, db
app = create_app()
with app.app_context():
    db.create_all()
    print('Database tables created successfully')
"
    
    print_success "Database migrations completed"
}

# Function to test the application
test_application() {
    print_status "Testing application..."
    
    # Start the application
    docker-compose up -d
    
    # Wait for application to be ready
    print_status "Waiting for application to be ready..."
    sleep 10
    
    # Test health endpoint
    if curl -f http://localhost:5000/health >/dev/null 2>&1; then
        print_success "Application is running successfully"
        print_success "Access the application at: http://localhost:5000"
    else
        print_error "Application failed to start properly"
        exit 1
    fi
}

# Function to show next steps
show_next_steps() {
    echo
    print_success "DockSafe setup completed successfully!"
    echo
    echo "Next steps:"
    echo "1. Access the web interface: http://localhost:5000"
    echo "2. Configure notification settings in the .env file"
    echo "3. Set up CI/CD integration using the provided templates"
    echo "4. Review the documentation for advanced configuration"
    echo
    echo "Useful commands:"
    echo "  Start services: docker-compose up -d"
    echo "  Stop services:  docker-compose down"
    echo "  View logs:      docker-compose logs -f"
    echo "  Update Trivy:   docker-compose exec docksafe trivy image --download-db-only"
    echo
}

# Main setup function
main() {
    echo "=========================================="
    echo "    DockSafe Setup Script"
    echo "=========================================="
    echo
    
    # Check prerequisites
    print_status "Checking prerequisites..."
    check_docker
    check_docker_compose
    check_trivy
    
    # Create necessary files and directories
    print_status "Setting up project structure..."
    create_env_file
    create_logs_directory
    
    # Setup database
    setup_database
    
    # Run migrations
    run_migrations
    
    # Test application
    test_application
    
    # Show next steps
    show_next_steps
}

# Run main function
main "$@"
