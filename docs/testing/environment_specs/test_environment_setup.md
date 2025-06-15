# Test Environment Setup - License Plate Recognition System

## Overview

This document provides comprehensive instructions for setting up test environments for the LPR system automation testing framework. It includes environment configurations, infrastructure requirements, and setup procedures for different testing scenarios.

## Environment Types

### 1. Local Development Environment
### 2. CI/CD Pipeline Environment  
### 3. Integration Testing Environment
### 4. Performance Testing Environment
### 5. Staging Environment
### 6. Production-like Environment

---

## 1. Local Development Environment

### System Requirements

#### Minimum Hardware Requirements
```yaml
hardware_specs:
  cpu: 4_cores_minimum (8_cores_recommended)
  memory: 8GB_minimum (16GB_recommended)
  storage: 100GB_available_space
  network: 100Mbps_connection
  gpu: Optional (NVIDIA_GPU_for_ML_acceleration)
  
operating_systems:
  supported:
    - Windows_10/11
    - macOS_12+
    - Ubuntu_20.04+
    - CentOS_8+
  recommended: Ubuntu_22.04_LTS
```

#### Software Dependencies
```yaml
required_software:
  docker: ">=20.10.0"
  docker_compose: ">=2.0.0"
  java: ">=17" (for automation framework)
  maven: ">=3.8.0"
  git: ">=2.30.0"
  
optional_software:
  ide: IntelliJ_IDEA or Eclipse
  browser: Chrome_latest, Firefox_latest
  postman: API_testing_tool
  dbeaver: Database_client
```

### Local Setup Instructions

#### Step 1: Repository Setup
```bash
# Clone the main application repository
git clone https://github.com/your-org/plate_recognition.git
cd plate_recognition

# Clone the automation testing repository
git clone https://github.com/your-org/plate_recognition_automation.git
cd plate_recognition_automation

# Create local configuration
cp .env.example .env.local
```

#### Step 2: Docker Environment Setup
```yaml
# docker-compose.local.yml
version: '3.8'
services:
  lpr-app:
    build:
      context: ../plate_recognition
      dockerfile: Dockerfile
    ports:
      - "8001:8001"
    environment:
      - ENVIRONMENT=test
      - DATABASE_URL=sqlite:///data/test_license_plates.db
      - LOG_LEVEL=DEBUG
    volumes:
      - ./test_data:/app/test_data
      - ./logs:/app/logs
    depends_on:
      - test-database
      - mock-services

  test-database:
    image: sqlite:latest
    volumes:
      - ./test_db:/var/lib/sqlite
    environment:
      - SQLITE_DATABASE=test_license_plates.db

  mock-services:
    build:
      context: ./mock_services
      dockerfile: Dockerfile
    ports:
      - "8080:8080"  # Mock webhook server
      - "8081:8081"  # Mock external APIs
    environment:
      - MOCK_MODE=development

  selenium-hub:
    image: selenium/hub:latest
    ports:
      - "4444:4444"

  selenium-chrome:
    image: selenium/node-chrome:latest
    environment:
      - HUB_HOST=selenium-hub
    depends_on:
      - selenium-hub

  selenium-firefox:
    image: selenium/node-firefox:latest
    environment:
      - HUB_HOST=selenium-hub
    depends_on:
      - selenium-hub
```

#### Step 3: Test Data Setup
```bash
# Generate test data
cd test_data_generator
python generate_test_data.py --environment=local --size=small

# Seed test database
python seed_database.py --config=local_config.json

# Verify test data
python validate_test_data.py --data_path=./test_data
```

#### Step 4: Environment Validation
```bash
# Start all services
docker-compose -f docker-compose.local.yml up -d

# Wait for services to be ready
./scripts/wait_for_services.sh

# Run environment validation tests
mvn test -Dtest=EnvironmentValidationTest
```

---

## 2. CI/CD Pipeline Environment

### GitHub Actions Configuration

#### Workflow File Structure
```yaml
# .github/workflows/test-automation.yml
name: Test Automation Pipeline

on:
  pull_request:
    branches: [main, develop]
  push:
    branches: [main]
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM

env:
  JAVA_VERSION: '17'
  MAVEN_VERSION: '3.8.6'
  DOCKER_BUILDKIT: 1

jobs:
  setup-test-environment:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4
        
      - name: Setup Java
        uses: actions/setup-java@v3
        with:
          java-version: ${{ env.JAVA_VERSION }}
          distribution: 'temurin'
          
      - name: Cache Maven Dependencies
        uses: actions/cache@v3
        with:
          path: ~/.m2
          key: ${{ runner.os }}-m2-${{ hashFiles('**/pom.xml') }}
          
      - name: Setup Docker Buildx
        uses: docker/setup-buildx-action@v2
        
      - name: Build Test Environment
        run: |
          docker-compose -f docker-compose.ci.yml build
          docker-compose -f docker-compose.ci.yml up -d
          
      - name: Wait for Services
        run: ./scripts/wait_for_services.sh
        timeout-minutes: 5

  unit-tests:
    needs: setup-test-environment
    runs-on: ubuntu-latest
    steps:
      - name: Run Unit Tests
        run: mvn test -Dtest=UnitTestSuite
        
      - name: Generate Test Report
        uses: dorny/test-reporter@v1
        if: success() || failure()
        with:
          name: Unit Test Results
          path: target/surefire-reports/*.xml
          reporter: java-junit

  integration-tests:
    needs: setup-test-environment
    runs-on: ubuntu-latest
    strategy:
      matrix:
        test-group: [api, database, services, websocket]
    steps:
      - name: Run Integration Tests - ${{ matrix.test-group }}
        run: |
          mvn test -Dtest=IntegrationTestSuite \
                   -Dgroups=${{ matrix.test-group }} \
                   -Dparallel=methods \
                   -DthreadCount=4

  ui-tests:
    needs: setup-test-environment
    runs-on: ubuntu-latest
    strategy:
      matrix:
        browser: [chrome, firefox, edge]
    steps:
      - name: Run UI Tests - ${{ matrix.browser }}
        run: |
          mvn test -Dtest=UITestSuite \
                   -Dbrowser=${{ matrix.browser }} \
                   -Dheadless=true \
                   -Dparallel=classes

  performance-tests:
    needs: setup-test-environment
    runs-on: ubuntu-latest
    if: github.event_name == 'schedule' || contains(github.event.pull_request.labels.*.name, 'performance')
    steps:
      - name: Run Performance Tests
        run: |
          mvn test -Dtest=PerformanceTestSuite \
                   -Dperformance.duration=300 \
                   -Dperformance.users=50

  security-tests:
    needs: setup-test-environment
    runs-on: ubuntu-latest
    steps:
      - name: Run Security Tests
        run: mvn test -Dtest=SecurityTestSuite
        
      - name: Upload Security Report
        uses: actions/upload-artifact@v3
        with:
          name: security-test-report
          path: target/security-reports/

  test-reporting:
    needs: [unit-tests, integration-tests, ui-tests, performance-tests, security-tests]
    runs-on: ubuntu-latest
    if: always()
    steps:
      - name: Generate Consolidated Report
        run: |
          mvn allure:report
          mvn site
          
      - name: Upload Test Results
        uses: actions/upload-artifact@v3
        with:
          name: test-results
          path: target/site/
          
      - name: Comment PR with Results
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v6
        with:
          script: |
            const testResults = require('./test-summary.json');
            const comment = `## Test Results Summary
            - ✅ Unit Tests: ${testResults.unit.passed}/${testResults.unit.total}
            - ✅ Integration Tests: ${testResults.integration.passed}/${testResults.integration.total}  
            - ✅ UI Tests: ${testResults.ui.passed}/${testResults.ui.total}
            - ⚡ Performance Tests: ${testResults.performance.status}
            - 🔒 Security Tests: ${testResults.security.status}`;
            
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: comment
            });

  cleanup:
    needs: test-reporting
    runs-on: ubuntu-latest
    if: always()
    steps:
      - name: Cleanup Test Environment
        run: |
          docker-compose -f docker-compose.ci.yml down -v
          docker system prune -f
```

#### CI Environment Configuration
```yaml
# docker-compose.ci.yml
version: '3.8'
services:
  lpr-app:
    build:
      context: .
      dockerfile: Dockerfile.test
    environment:
      - ENVIRONMENT=ci
      - DATABASE_URL=sqlite:///tmp/test.db
      - LOG_LEVEL=INFO
      - DISABLE_GPU=true
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/api/system/health"]
      interval: 10s
      timeout: 5s
      retries: 5

  test-database:
    image: sqlite:alpine
    tmpfs:
      - /tmp/db

  selenium-grid:
    image: selenium/standalone-chrome:latest
    shm_size: 2gb
    environment:
      - SE_OPTS=--enable-managed-downloads
    ports:
      - "4444:4444"

  performance-monitor:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
```

---

## 3. Integration Testing Environment

### Multi-Service Environment Setup

#### Docker Compose Configuration
```yaml
# docker-compose.integration.yml
version: '3.8'
services:
  lpr-app-primary:
    build: .
    ports:
      - "8001:8001"
    environment:
      - INSTANCE_ID=primary
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/lpr_test
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy

  lpr-app-secondary:
    build: .
    ports:
      - "8002:8001"
    environment:
      - INSTANCE_ID=secondary
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/lpr_test
    depends_on:
      postgres:
        condition: service_healthy

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=lpr_test
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./sql/init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  nginx-lb:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - lpr-app-primary
      - lpr-app-secondary

  mock-camera-service:
    build: ./mock_services/camera
    ports:
      - "8554:8554"  # RTSP server
    environment:
      - CAMERA_COUNT=4
      - STREAM_FORMAT=rtsp

  mock-webhook-service:
    build: ./mock_services/webhook
    ports:
      - "8080:8080"
    environment:
      - WEBHOOK_DELAY=100ms
      - WEBHOOK_SUCCESS_RATE=0.95

volumes:
  postgres_data:
  redis_data:
```

#### Integration Test Configuration
```yaml
# integration-test-config.yml
test_environment:
  application_urls:
    primary: "http://localhost:8001"
    secondary: "http://localhost:8002"
    load_balancer: "http://localhost"
    
  database:
    host: "localhost"
    port: 5432
    database: "lpr_test"
    username: "postgres"
    password: "password"
    
  mock_services:
    camera_service: "rtsp://localhost:8554"
    webhook_service: "http://localhost:8080"
    
  test_data:
    images_path: "./test_data/images"
    videos_path: "./test_data/videos"
    database_seed: "./test_data/database_seed.sql"
    
test_scenarios:
  load_balancing:
    enabled: true
    strategy: "round_robin"
    
  database_failover:
    enabled: true
    simulation: "connection_loss"
    
  service_communication:
    timeout: 30s
    retry_attempts: 3
```

---

## 4. Performance Testing Environment

### High-Performance Infrastructure

#### Hardware Specifications
```yaml
performance_environment:
  application_server:
    cpu: 16_cores
    memory: 32GB
    storage: 1TB_NVMe_SSD
    network: 10Gbps
    gpu: NVIDIA_RTX_4090 (optional)
    
  database_server:
    cpu: 8_cores
    memory: 16GB
    storage: 500GB_SSD
    network: 10Gbps
    
  load_generators:
    count: 3
    cpu_per_instance: 8_cores
    memory_per_instance: 16GB
    network: 1Gbps_each
    
  monitoring_server:
    cpu: 4_cores
    memory: 8GB
    storage: 200GB_SSD
```

#### Performance Test Setup
```yaml
# docker-compose.performance.yml
version: '3.8'
services:
  lpr-app:
    build:
      context: .
      dockerfile: Dockerfile.performance
    deploy:
      resources:
        limits:
          cpus: '16'
          memory: 32G
        reservations:
          cpus: '8'
          memory: 16G
    environment:
      - ENVIRONMENT=performance
      - MAX_WORKERS=16
      - WORKER_MEMORY=2G
      - GPU_ENABLED=true
    ports:
      - "8001:8001"

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards

  jmeter-master:
    build: ./jmeter
    environment:
      - JMETER_MODE=master
    volumes:
      - ./performance_tests:/tests
      - jmeter_results:/results

  jmeter-slave-1:
    build: ./jmeter
    environment:
      - JMETER_MODE=slave
      - JMETER_MASTER=jmeter-master

  jmeter-slave-2:
    build: ./jmeter
    environment:
      - JMETER_MODE=slave
      - JMETER_MASTER=jmeter-master

  jmeter-slave-3:
    build: ./jmeter
    environment:
      - JMETER_MODE=slave
      - JMETER_MASTER=jmeter-master

volumes:
  prometheus_data:
  grafana_data:
  jmeter_results:
```

#### Performance Monitoring Configuration
```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 5s
  evaluation_interval: 5s

scrape_configs:
  - job_name: 'lpr-application'
    static_configs:
      - targets: ['lpr-app:8001']
    metrics_path: '/metrics'
    scrape_interval: 1s

  - job_name: 'system-metrics'
    static_configs:
      - targets: ['node-exporter:9100']

rule_files:
  - "alert_rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

---

## 5. Staging Environment

### Production-like Configuration

#### Infrastructure Setup
```yaml
# docker-compose.staging.yml
version: '3.8'
services:
  lpr-app:
    image: lpr-app:latest
    deploy:
      replicas: 2
      update_config:
        parallelism: 1
        delay: 10s
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
    environment:
      - ENVIRONMENT=staging
      - DATABASE_URL=postgresql://user:pass@db-staging:5432/lpr_staging
      - REDIS_URL=redis://redis-staging:6379
      - LOG_LEVEL=INFO
    networks:
      - app-network

  nginx:
    image: nginx:alpine
    ports:
      - "443:443"
      - "80:80"
    volumes:
      - ./nginx/staging.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - lpr-app
    networks:
      - app-network

  db-staging:
    image: postgres:15
    environment:
      - POSTGRES_DB=lpr_staging
      - POSTGRES_USER=lpr_user
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_staging:/var/lib/postgresql/data
    networks:
      - db-network

  redis-staging:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_staging:/data
    networks:
      - app-network

networks:
  app-network:
    driver: bridge
  db-network:
    driver: bridge

volumes:
  postgres_staging:
  redis_staging:
```

#### Environment Configuration
```yaml
# staging-config.yml
environment: staging

database:
  connection_pool_size: 20
  max_overflow: 30
  pool_timeout: 30
  pool_recycle: 3600

cache:
  redis_cluster: true
  max_connections: 100
  socket_timeout: 5

security:
  ssl_enabled: true
  certificate_path: "/etc/nginx/ssl/staging.crt"
  private_key_path: "/etc/nginx/ssl/staging.key"
  
monitoring:
  metrics_enabled: true
  logging_level: "INFO"
  health_check_interval: 30s
  
backup:
  database_backup_schedule: "0 2 * * *"
  retention_days: 30
  backup_location: "s3://staging-backups/"
```

---

## 6. Production-like Environment

### Full Production Simulation

#### Kubernetes Configuration
```yaml
# k8s/production-like/namespace.yml
apiVersion: v1
kind: Namespace
metadata:
  name: lpr-test

---
# k8s/production-like/deployment.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: lpr-app
  namespace: lpr-test
spec:
  replicas: 3
  selector:
    matchLabels:
      app: lpr-app
  template:
    metadata:
      labels:
        app: lpr-app
    spec:
      containers:
      - name: lpr-app
        image: lpr-app:latest
        ports:
        - containerPort: 8001
        env:
        - name: ENVIRONMENT
          value: "production-like"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: lpr-secrets
              key: database-url
        resources:
          requests:
            cpu: 1000m
            memory: 2Gi
          limits:
            cpu: 2000m
            memory: 4Gi
        livenessProbe:
          httpGet:
            path: /api/system/health
            port: 8001
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/system/ready
            port: 8001
          initialDelaySeconds: 10
          periodSeconds: 5

---
# k8s/production-like/service.yml
apiVersion: v1
kind: Service
metadata:
  name: lpr-service
  namespace: lpr-test
spec:
  selector:
    app: lpr-app
  ports:
  - port: 80
    targetPort: 8001
  type: ClusterIP

---
# k8s/production-like/ingress.yml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: lpr-ingress
  namespace: lpr-test
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - lpr-test.example.com
    secretName: lpr-tls
  rules:
  - host: lpr-test.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: lpr-service
            port:
              number: 80
```

#### Production-like Test Configuration
```yaml
# production-like-test-config.yml
cluster:
  provider: "kubernetes"
  namespace: "lpr-test"
  replicas: 3
  
load_balancer:
  type: "nginx-ingress"
  ssl_termination: true
  rate_limiting: true
  
database:
  type: "postgresql"
  high_availability: true
  backup_enabled: true
  monitoring: true
  
monitoring:
  prometheus: true
  grafana: true
  alerting: true
  log_aggregation: true
  
security:
  network_policies: true
  pod_security_policies: true
  rbac: true
  secrets_management: true
```

---

## Environment Management

### Environment Lifecycle

#### Setup Scripts
```bash
#!/bin/bash
# setup_test_environment.sh

set -e

ENVIRONMENT=${1:-local}
CONFIG_DIR="./config/${ENVIRONMENT}"

echo "Setting up ${ENVIRONMENT} test environment..."

# Validate environment
if [ ! -d "${CONFIG_DIR}" ]; then
    echo "Error: Configuration directory ${CONFIG_DIR} not found"
    exit 1
fi

# Load environment-specific configuration
source "${CONFIG_DIR}/env.sh"

# Create necessary directories
mkdir -p logs test_data/{images,videos,database} reports

# Generate test data
echo "Generating test data..."
python scripts/generate_test_data.py --environment=${ENVIRONMENT}

# Start services
echo "Starting services..."
docker-compose -f "docker-compose.${ENVIRONMENT}.yml" up -d

# Wait for services to be ready
echo "Waiting for services to be ready..."
./scripts/wait_for_services.sh --timeout=300

# Run health checks
echo "Running health checks..."
./scripts/health_check.sh

# Seed test data
echo "Seeding test database..."
python scripts/seed_database.py --config="${CONFIG_DIR}/database.yml"

echo "Test environment ${ENVIRONMENT} is ready!"
```

#### Health Check Script
```bash
#!/bin/bash
# scripts/health_check.sh

check_service() {
    local service_name=$1
    local health_url=$2
    local max_attempts=${3:-30}
    local wait_time=${4:-5}
    
    echo "Checking health of ${service_name}..."
    
    for ((i=1; i<=max_attempts; i++)); do
        if curl -f -s "${health_url}" > /dev/null 2>&1; then
            echo "✅ ${service_name} is healthy"
            return 0
        fi
        
        echo "⏳ Attempt ${i}/${max_attempts}: ${service_name} not ready, waiting ${wait_time}s..."
        sleep ${wait_time}
    done
    
    echo "❌ ${service_name} health check failed after ${max_attempts} attempts"
    return 1
}

# Check all services
check_service "LPR Application" "http://localhost:8001/api/system/health"
check_service "Database" "http://localhost:8001/api/system/db-health"
check_service "Selenium Grid" "http://localhost:4444/status"

if [ "$?" -eq 0 ]; then
    echo "🎉 All services are healthy!"
else
    echo "💥 Some services are not healthy. Check logs for details."
    exit 1
fi
```

#### Cleanup Script
```bash
#!/bin/bash
# scripts/cleanup_environment.sh

ENVIRONMENT=${1:-local}
FORCE=${2:-false}

echo "Cleaning up ${ENVIRONMENT} test environment..."

if [ "${FORCE}" == "true" ]; then
    echo "Force cleanup mode enabled"
else
    read -p "Are you sure you want to cleanup the environment? (y/N): " confirm
    if [ "${confirm}" != "y" ] && [ "${confirm}" != "Y" ]; then
        echo "Cleanup cancelled"
        exit 0
    fi
fi

# Stop and remove containers
docker-compose -f "docker-compose.${ENVIRONMENT}.yml" down -v

# Remove test data (optional)
if [ "${FORCE}" == "true" ]; then
    rm -rf test_data/* logs/* reports/*
    echo "Test data and logs cleaned up"
fi

# Prune Docker resources
docker system prune -f

echo "Environment cleanup completed"
```

### Environment Variables Management

#### Environment Configuration Template
```bash
# config/local/env.sh
export ENVIRONMENT=local
export LOG_LEVEL=DEBUG
export DATABASE_URL=sqlite:///data/test_license_plates.db
export REDIS_URL=redis://localhost:6379
export SELENIUM_HUB_URL=http://localhost:4444
export API_BASE_URL=http://localhost:8001
export WEBHOOK_BASE_URL=http://localhost:8080
export TEST_DATA_PATH=./test_data
export REPORT_OUTPUT_PATH=./reports
export PARALLEL_EXECUTION=true
export MAX_THREADS=4
export DEFAULT_TIMEOUT=30
export RETRY_ATTEMPTS=3
export SCREENSHOT_ON_FAILURE=true
export VIDEO_RECORDING=false
export HEADLESS_BROWSER=false
```

#### Secrets Management
```yaml
# secrets/local-secrets.yml (encrypted)
database:
  username: test_user
  password: test_password_123
  
api_keys:
  test_api_key: test_api_key_local_12345
  webhook_token: webhook_token_local_67890
  
external_services:
  license_validation_api_key: mock_api_key
  vehicle_database_token: mock_db_token
```

### Environment Validation

#### Validation Checklist
```yaml
environment_validation:
  services:
    - name: "LPR Application"
      url: "${API_BASE_URL}/api/system/health"
      expected_status: 200
      timeout: 30s
      
    - name: "Database Connection"
      url: "${API_BASE_URL}/api/system/db-health"
      expected_status: 200
      timeout: 10s
      
    - name: "Selenium Grid"
      url: "${SELENIUM_HUB_URL}/status"
      expected_status: 200
      timeout: 15s
      
  test_data:
    - path: "${TEST_DATA_PATH}/images"
      min_files: 100
      file_types: [".jpg", ".png"]
      
    - path: "${TEST_DATA_PATH}/videos"
      min_files: 10
      file_types: [".mp4", ".avi"]
      
  database:
    - table: "detections"
      min_records: 1000
      
    - table: "cameras" 
      min_records: 4
      
  configuration:
    - env_var: "API_BASE_URL"
      required: true
      
    - env_var: "DATABASE_URL"
      required: true
      
    - env_var: "SELENIUM_HUB_URL"
      required: true
```

This comprehensive test environment setup documentation provides everything needed to establish consistent, reliable test environments across different stages of the development and testing lifecycle. Each environment is tailored for its specific purpose while maintaining consistency in configuration and management approaches.