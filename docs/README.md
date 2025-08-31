# DockSafe Documentation

## Table of Contents

1. [Overview](#overview)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Usage](#usage)
5. [API Reference](#api-reference)
6. [CI/CD Integration](#cicd-integration)
7. [Troubleshooting](#troubleshooting)
8. [Development](#development)

## Overview

DockSafe is an automated container image vulnerability scanner designed to integrate seamlessly into CI/CD pipelines. It provides real-time vulnerability scanning, comprehensive reporting, and historical tracking capabilities.

### Key Features

- **Automated Vulnerability Scanning**: Uses Trivy and Clair to scan container images
- **CI/CD Integration**: Works with Jenkins, GitHub Actions, and GitLab CI
- **Real-time Notifications**: Slack, Teams, and email notifications
- **Web Dashboard**: Track vulnerability trends and scan history
- **Exception Management**: Handle approved vulnerabilities with proper workflows
- **Comprehensive Reporting**: Generate reports in multiple formats

### Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   CI/CD Pipeline│    │  Vulnerability  │    │   Notification  │
│   (Jenkins/     │───▶│    Scanner      │───▶│    System       │
│   GitHub Actions)│    │   (Trivy/Clair) │    │  (Slack/Teams)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Web Dashboard │
                       │   (Grafana/     │
                       │   Custom UI)    │
                       └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Metrics DB    │
                       │  (Prometheus)   │
                       └─────────────────┘
```

## Installation

### Prerequisites

- Docker and Docker Compose
- Python 3.11+
- Trivy vulnerability scanner
- PostgreSQL (optional, can use SQLite for development)

### Quick Start

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd DockSafe
   ```

2. **Run the setup script**:
   ```bash
   ./scripts/setup.sh
   ```

3. **Access the application**:
   - Web Interface: http://localhost:5000
   - API Documentation: http://localhost:5000/api/v1

### Manual Installation

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Install Trivy**:
   ```bash
   # Ubuntu/Debian
   wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | sudo apt-key add -
   echo deb https://aquasecurity.github.io/trivy-repo/deb $(lsb_release -sc) main | sudo tee -a /etc/apt/sources.list.d/trivy.list
   sudo apt-get update
   sudo apt-get install -y trivy

   # macOS
   brew install trivy
   ```

3. **Set up database**:
   ```bash
   # Using Docker Compose
   docker-compose up -d postgres
   
   # Or configure your own PostgreSQL instance
   ```

4. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Initialize database**:
   ```bash
   python -c "
   from app import create_app, db
   app = create_app()
   with app.app_context():
       db.create_all()
   "
   ```

6. **Run the application**:
   ```bash
   python run.py
   ```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_ENV` | Flask environment | `development` |
| `SECRET_KEY` | Flask secret key | Auto-generated |
| `DATABASE_URL` | Database connection string | PostgreSQL |
| `SCANNER_TYPE` | Vulnerability scanner type | `trivy` |
| `SCANNER_TIMEOUT` | Scan timeout in seconds | `300` |
| `VULNERABILITY_THRESHOLD` | Minimum severity threshold | `HIGH` |
| `SLACK_WEBHOOK_URL` | Slack webhook URL | None |
| `TEAMS_WEBHOOK_URL` | Teams webhook URL | None |
| `EMAIL_SMTP_SERVER` | SMTP server for email notifications | None |
| `EMAIL_SMTP_PORT` | SMTP port | `587` |
| `EMAIL_USERNAME` | Email username | None |
| `EMAIL_PASSWORD` | Email password | None |
| `PROMETHEUS_ENABLED` | Enable Prometheus metrics | `true` |
| `GRAFANA_URL` | Grafana URL | `http://localhost:3000` |
| `LOG_LEVEL` | Logging level | `INFO` |

### Scanner Configuration

#### Trivy Configuration

Trivy is the default scanner. Configuration options:

```yaml
scanner_type: trivy
timeout: 300
severity_threshold: HIGH
format: json
```

#### Clair Configuration

Clair requires registry integration:

```yaml
scanner_type: clair
clair_url: http://localhost:6060
timeout: 300
```

## Usage

### Web Interface

1. **Dashboard**: View scan statistics and trends
2. **Scanner**: Manually scan container images
3. **Reports**: Generate and download vulnerability reports
4. **Notifications**: Configure and test notification settings
5. **Exceptions**: Manage approved vulnerabilities

### API Usage

#### Scan an Image

```bash
curl -X POST http://localhost:5000/scanner/scan \
  -H "Content-Type: application/json" \
  -d '{
    "image_name": "nginx",
    "image_tag": "latest"
  }'
```

#### Get Scan Results

```bash
curl http://localhost:5000/scanner/scan/1
```

#### Get Scan History

```bash
curl http://localhost:5000/scanner/history?limit=10
```

#### Get Statistics

```bash
curl http://localhost:5000/scanner/statistics?days=30
```

### Command Line Interface

```bash
# Scan an image
python -m app.scanner.cli scan nginx:latest

# Get scan history
python -m app.scanner.cli history

# Generate report
python -m app.scanner.cli report --scan-id 1 --format pdf
```

## API Reference

### Scanner Endpoints

#### POST /scanner/scan

Scan a container image for vulnerabilities.

**Request Body**:
```json
{
  "image_name": "string",
  "image_tag": "string (optional, default: latest)"
}
```

**Response**:
```json
{
  "message": "Scan completed successfully",
  "scan_id": 1,
  "scan_status": "SUCCESS",
  "total_vulnerabilities": 5,
  "severity_breakdown": {
    "critical": 0,
    "high": 2,
    "medium": 2,
    "low": 1
  },
  "scan_duration_seconds": 45,
  "should_fail_build": true
}
```

#### GET /scanner/scan/{scan_id}

Get detailed scan results.

**Response**:
```json
{
  "scan": {
    "id": 1,
    "image_name": "nginx",
    "image_tag": "latest",
    "scan_status": "SUCCESS",
    "total_vulnerabilities": 5,
    "critical_count": 0,
    "high_count": 2,
    "medium_count": 2,
    "low_count": 1,
    "scan_duration_seconds": 45,
    "scanner_version": "0.48.3",
    "created_at": "2025-01-15T10:30:00Z"
  },
  "vulnerabilities": [
    {
      "id": 1,
      "cve_id": "CVE-2024-1234",
      "severity": "HIGH",
      "package_name": "openssl",
      "package_version": "1.1.1f",
      "fixed_version": "1.1.1g",
      "description": "Vulnerability description",
      "cvss_score": 8.5,
      "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"
    }
  ],
  "should_fail_build": true
}
```

#### GET /scanner/history

Get scan history with optional filtering.

**Query Parameters**:
- `image_name` (optional): Filter by image name
- `limit` (optional): Number of results (default: 50)

#### GET /scanner/statistics

Get scan statistics for a time period.

**Query Parameters**:
- `days` (optional): Number of days (default: 30)

### Exception Management

#### GET /scanner/exceptions

Get scan exceptions.

#### POST /scanner/exceptions

Create a new exception.

**Request Body**:
```json
{
  "cve_id": "CVE-2024-1234",
  "image_name": "nginx (optional, null for global)",
  "reason": "Approved for business reasons",
  "approved_by": "security-team",
  "expires_at": "2025-12-31T23:59:59Z (optional)",
  "is_active": true
}
```

## CI/CD Integration

### GitHub Actions

```yaml
name: Vulnerability Scan
on: [push, pull_request]

jobs:
  vulnerability-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build Docker image
        run: docker build -t myapp:${{ github.sha }} .
      - name: Run vulnerability scan
        run: |
          curl -X POST http://docksafe:5000/scanner/scan \
            -H "Content-Type: application/json" \
            -d '{"image_name": "myapp", "image_tag": "${{ github.sha }}"}'
```

### Jenkins Pipeline

```groovy
pipeline {
    agent any
    stages {
        stage('Build') {
            steps {
                sh 'docker build -t myapp:${BUILD_NUMBER} .'
            }
        }
        stage('Vulnerability Scan') {
            steps {
                script {
                    def scanResult = httpRequest(
                        url: 'http://docksafe:5000/scanner/scan',
                        httpMode: 'POST',
                        contentType: 'APPLICATION_JSON',
                        requestBody: """
                        {
                            "image_name": "myapp",
                            "image_tag": "${env.BUILD_NUMBER}"
                        }
                        """
                    )
                    
                    def scanData = readJSON text: scanResult.content
                    if (scanData.should_fail_build) {
                        error "Vulnerabilities detected! Build failed."
                    }
                }
            }
        }
    }
}
```

### GitLab CI

```yaml
vulnerability_scan:
  stage: test
  script:
    - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .
    - |
      curl -X POST http://docksafe:5000/scanner/scan \
        -H "Content-Type: application/json" \
        -d "{\"image_name\": \"$CI_REGISTRY_IMAGE\", \"image_tag\": \"$CI_COMMIT_SHA\"}"
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
```

## Troubleshooting

### Common Issues

#### Scanner Not Available

**Problem**: Scanner service returns 503 error.

**Solution**:
1. Check if Trivy is installed: `trivy --version`
2. Verify scanner configuration in `.env`
3. Check scanner logs: `docker-compose logs docksafe`

#### Database Connection Issues

**Problem**: Application fails to connect to database.

**Solution**:
1. Verify PostgreSQL is running: `docker-compose ps postgres`
2. Check database URL in `.env`
3. Ensure database is initialized: `docker-compose exec postgres psql -U docksafe -d docksafe`

#### Scan Timeout

**Problem**: Scans take too long or timeout.

**Solution**:
1. Increase timeout in configuration
2. Check network connectivity
3. Verify image is accessible
4. Consider using smaller base images

#### Notification Failures

**Problem**: Notifications are not being sent.

**Solution**:
1. Verify webhook URLs are correct
2. Check network connectivity to external services
3. Review notification logs
4. Test notifications manually

### Logs

View application logs:

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f docksafe

# Application logs
tail -f logs/docksafe.log
```

### Health Checks

Check system health:

```bash
# Application health
curl http://localhost:5000/health

# Database health
docker-compose exec postgres pg_isready -U docksafe -d docksafe

# Scanner health
trivy --version
```

## Development

### Project Structure

```
DockSafe/
├── app/
│   ├── scanner/          # Vulnerability scanning
│   ├── reports/          # Report generation
│   ├── notifications/    # Notification services
│   ├── dashboard/        # Web dashboard
│   ├── api/             # API endpoints
│   ├── models.py        # Database models
│   └── config.py        # Configuration
├── ci/                  # CI/CD templates
├── docs/               # Documentation
├── scripts/            # Setup and utility scripts
├── tests/              # Test suite
├── docker-compose.yml  # Docker services
├── Dockerfile          # Application container
└── requirements.txt    # Python dependencies
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_scanner.py
```

### Code Style

```bash
# Format code
black app/

# Lint code
flake8 app/

# Type checking
mypy app/
```

### Adding New Features

1. Create feature branch
2. Implement feature with tests
3. Update documentation
4. Submit pull request

### Contributing

1. Fork the repository
2. Create feature branch
3. Make changes with tests
4. Update documentation
5. Submit pull request

## Support

For support and questions:

- Create an issue on GitHub
- Check the troubleshooting section
- Review the API documentation
- Contact the development team

## License

This project is licensed under the MIT License - see the LICENSE file for details.
