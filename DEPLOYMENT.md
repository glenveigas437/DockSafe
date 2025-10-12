# DockSafe - Container Vulnerability Scanner

A comprehensive container image vulnerability scanning platform with modern CI/CD pipeline and infrastructure as code.

## 🚀 Features

- **Multi-Scanner Support**: Trivy and Clair vulnerability scanners
- **Group-Based Access Control**: Multi-tenant architecture with role-based permissions
- **Modern UI**: Clean, responsive interface built with Tailwind CSS
- **Google SSO**: Secure authentication with Google OAuth 2.0
- **Real-time Notifications**: Slack and email notifications
- **Comprehensive Reporting**: Detailed vulnerability reports with pagination
- **Dockerized**: Complete containerization for easy deployment
- **CI/CD Pipeline**: Automated testing, building, and deployment
- **Infrastructure as Code**: Terraform and Ansible for infrastructure management
- **Kubernetes Ready**: Full Kubernetes manifests for container orchestration

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │    │   DockSafe App  │    │   PostgreSQL    │
│   (Nginx)       │────│   (Flask)       │────│   Database      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                       ┌─────────────────┐    ┌─────────────────┐
                       │     Redis       │    │   Trivy Scanner │
                       │   (Caching)     │    │   (Vulnerability)│
                       └─────────────────┘    └─────────────────┘
```

## 📋 Prerequisites

- Docker & Docker Compose
- Python 3.11+
- Node.js 18+ (for Tailwind CSS)
- Git
- AWS CLI (for Terraform)
- kubectl (for Kubernetes deployment)
- Ansible (for server deployment)

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/docksafe.git
cd docksafe
```

### 2. Environment Setup

```bash
# Copy environment template
cp .env.example .env

# Edit environment variables
nano .env
```

### 3. Local Development

```bash
# Start development environment
docker-compose up -d

# Run database migrations
docker-compose exec docksafe-app flask db upgrade

# Access the application
open http://localhost
```

### 4. Production Deployment

```bash
# Make deployment script executable
chmod +x scripts/deploy.sh

# Deploy to production
./scripts/deploy.sh latest production docker-compose
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_ENV` | Flask environment | `production` |
| `SECRET_KEY` | Flask secret key | Required |
| `DATABASE_URL` | Database connection string | Required |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID | Required |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret | Required |
| `DOCSAFE_EMAIL_SMTP_SERVER` | SMTP server | `smtp.gmail.com` |
| `DOCSAFE_EMAIL_SMTP_PORT` | SMTP port | `587` |
| `DOCSAFE_EMAIL_USERNAME` | SMTP username | Required |
| `DOCSAFE_EMAIL_PASSWORD` | SMTP password | Required |

### Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Google+ API
4. Create OAuth 2.0 credentials
5. Add authorized redirect URIs:
   - `http://localhost:5000/auth/callback` (development)
   - `https://yourdomain.com/auth/callback` (production)

## 🐳 Docker Deployment

### Development

```bash
docker-compose up -d
```

### Production

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Custom Configuration

```bash
# Build custom image
docker build -t docksafe:custom .

# Run with custom configuration
docker run -d \
  --name docksafe \
  -p 5000:5000 \
  -e SECRET_KEY=your-secret-key \
  -e DATABASE_URL=postgresql://user:pass@host:5432/db \
  docksafe:custom
```

## ☸️ Kubernetes Deployment

### 1. Prepare Secrets

```bash
# Create secrets
kubectl create secret generic docksafe-secrets \
  --from-literal=SECRET_KEY=your-secret-key \
  --from-literal=DB_PASSWORD=your-db-password \
  --from-literal=GOOGLE_CLIENT_SECRET=your-google-secret \
  --from-literal=EMAIL_PASSWORD=your-email-password \
  -n docksafe
```

### 2. Deploy Application

```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/docksafe.yaml

# Check deployment status
kubectl get pods -n docksafe
kubectl get services -n docksafe
```

### 3. Access Application

```bash
# Get ingress URL
kubectl get ingress -n docksafe

# Port forward for local access
kubectl port-forward service/docksafe-service 8080:80 -n docksafe
```

## 🏗️ Infrastructure as Code

### Terraform Deployment

```bash
cd terraform

# Initialize Terraform
terraform init

# Plan deployment
terraform plan -var="environment=production"

# Apply infrastructure
terraform apply -var="environment=production"
```

### Ansible Deployment

```bash
cd ansible

# Deploy to production servers
ansible-playbook -i inventory.ini deploy.yml --limit production

# Deploy to staging
ansible-playbook -i inventory.ini deploy.yml --limit staging
```

## 🔄 CI/CD Pipeline

The GitHub Actions pipeline includes:

- **Code Quality**: Linting with flake8 and black
- **Testing**: Unit tests with pytest and coverage
- **Security**: Vulnerability scanning with Trivy
- **Building**: Docker image building and pushing
- **Deployment**: Automated deployment to staging/production

### Pipeline Triggers

- **Push to `main`**: Deploy to production
- **Push to `develop`**: Deploy to staging
- **Pull Request**: Run tests and security scans

## 📊 Monitoring

### Health Checks

- **Application**: `GET /health`
- **Database**: Connection status
- **Redis**: Cache status
- **Load Balancer**: Nginx health

### Metrics

- **Prometheus**: `http://localhost:9090`
- **Grafana**: `http://localhost:3000` (admin/admin123)

### Logs

```bash
# View application logs
docker-compose logs -f docksafe-app

# View all logs
docker-compose logs -f

# Kubernetes logs
kubectl logs -f deployment/docksafe-app -n docksafe
```

## 🔒 Security

### Security Features

- **HTTPS**: SSL/TLS encryption
- **Rate Limiting**: API rate limiting
- **Security Headers**: XSS, CSRF protection
- **Input Validation**: SQL injection prevention
- **Authentication**: Google OAuth 2.0
- **Authorization**: Role-based access control

### Security Scanning

```bash
# Run Trivy security scan
trivy image docksafe:latest

# Run in CI/CD pipeline
trivy fs .
```

## 🧪 Testing

### Unit Tests

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test
pytest tests/test_scanner.py
```

### Integration Tests

```bash
# Test with Docker Compose
docker-compose -f docker-compose.test.yml up --abort-on-container-exit
```

## 📈 Performance

### Optimization

- **Database**: Connection pooling, indexing
- **Caching**: Redis for session storage
- **Static Files**: CDN integration
- **Load Balancing**: Multiple app instances
- **Resource Limits**: CPU and memory limits

### Scaling

```bash
# Scale application instances
docker-compose up -d --scale docksafe-app=3

# Kubernetes scaling
kubectl scale deployment docksafe-app --replicas=5 -n docksafe
```

## 🛠️ Development

### Local Development Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt

# Run development server
python run.py

# Run tests
pytest

# Run linting
flake8 app/
black app/
```

### Code Style

- **Python**: PEP 8 with black formatting
- **JavaScript**: ESLint configuration
- **CSS**: Tailwind CSS utility classes
- **Documentation**: Google-style docstrings

## 📚 API Documentation

### Authentication

All API endpoints require authentication via Google OAuth 2.0.

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/api/scans` | List vulnerability scans |
| POST | `/api/scans` | Create new scan |
| GET | `/api/scans/{id}` | Get scan details |
| GET | `/api/reports` | List reports |
| GET | `/api/reports/{id}` | Get report details |

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [Wiki](https://github.com/your-username/docksafe/wiki)
- **Issues**: [GitHub Issues](https://github.com/your-username/docksafe/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/docksafe/discussions)

## 🎯 Roadmap

- [ ] Multi-cloud deployment support
- [ ] Advanced vulnerability correlation
- [ ] Machine learning-based risk assessment
- [ ] Integration with more scanners
- [ ] Advanced reporting and analytics
- [ ] Mobile application
- [ ] API rate limiting improvements
- [ ] Advanced monitoring and alerting

---

**DockSafe** - Secure your containers, secure your future! 🐳🔒
