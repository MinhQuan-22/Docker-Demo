# Hướng Dẫn Deployment

Tài liệu này cung cấp hướng dẫn chi tiết để triển khai ứng dụng Docker Topic 5 (Flask API + PostgreSQL) lên môi trường local và production.

## Mục Lục

1. [Prerequisites](#prerequisites)
2. [Local Deployment](#local-deployment)
3. [Production Deployment](#production-deployment)
4. [Health Checks](#health-checks)
5. [Monitoring và Logging](#monitoring-và-logging)
6. [Rollback Procedures](#rollback-procedures)
7. [Security Best Practices](#security-best-practices)

---

## Prerequisites

Trước khi bắt đầu deployment, đảm bảo bạn đã cài đặt các công cụ sau:

### Required Tools

| Tool           | Minimum Version | Purpose                                    |
| -------------- | --------------- | ------------------------------------------ |
| Docker         | 24.0+           | Container runtime để chạy ứng dụng         |
| Docker Compose | 2.20+           | Orchestration tool cho multi-service setup |
| Git            | 2.30+           | Version control để clone repository        |

### Kiểm Tra Phiên Bản

```bash
# Kiểm tra Docker version
docker --version
# Expected: Docker version 24.0.0 hoặc cao hơn

# Kiểm tra Docker Compose version
docker compose version
# Expected: Docker Compose version v2.20.0 hoặc cao hơn

# Kiểm tra Git version
git --version
# Expected: git version 2.30.0 hoặc cao hơn
```

### System Requirements

- **RAM:** Tối thiểu 2GB available memory
- **Disk Space:** Tối thiểu 1GB free space cho images và volumes
- **Network:** Ports 8080 và 5433 phải available (không bị process khác sử dụng)

---

## Local Deployment

Hướng dẫn triển khai ứng dụng trên môi trường local để development và testing.

### Bước 1: Clone Repository

```bash
# Clone repository về máy local
git clone <repository-url>
cd docker-topic5

# Kiểm tra cấu trúc project
ls -la
# Expected: api/, db/, docker-compose.yml, README.md, DEPLOYMENT.md
```

### Bước 2: Configure Environment Variables

Tạo file `.env` từ template `.env.example`:

```bash
# Copy template file
cp .env.example .env

# Edit file .env với editor của bạn
nano .env  # hoặc vim, code, etc.
```

**Nội dung file `.env` cho local development:**

```bash
# Database Configuration
DB_HOST=db
DB_PORT=5432
DB_NAME=fullstack_demo
DB_USER=fullstack_user
DB_PASSWORD=fullstack_pass
```

> **Lưu ý:** Các giá trị này phù hợp cho local development. Đối với production, xem phần [Production Deployment](#production-deployment).

### Bước 3: Build Docker Images

```bash
# Build images cho tất cả services
docker compose build

# Verify images đã được tạo
docker images | grep topic5
# Expected output:
# docker-topic5-api    latest    <image-id>    <time>    <size>
```

**Giải thích:**

- `docker compose build` sẽ build image cho `api` service từ `./api/Dockerfile`
- `db` service sử dụng pre-built image `postgres:16-alpine` nên không cần build

### Bước 4: Start Services

```bash
# Start tất cả services trong background mode
docker compose up -d

# Verify services đang chạy
docker compose ps
# Expected output:
# NAME         IMAGE                  STATUS         PORTS
# topic5_api   docker-topic5-api      Up             0.0.0.0:8080->8080/tcp
# topic5_db    postgres:16-alpine     Up (healthy)   0.0.0.0:5433->5432/tcp
```

**Giải thích các bước khởi động:**

1. Docker Compose tạo network mặc định cho services
2. `db` service start trước và chạy health check
3. `init.sql` được execute tự động để tạo tables và seed data
4. Khi `db` service healthy, `api` service mới start (do `depends_on` condition)
5. `api` service connect đến database và listen trên port 8080

### Bước 5: Verify Deployment

Kiểm tra các services hoạt động đúng:

```bash
# 1. Kiểm tra API health
curl http://localhost:8080/health
# Expected: {"status": "ok"}

# 2. Kiểm tra database connectivity
curl http://localhost:8080/db-check
# Expected: {"database": "connected", "message": "Database connection successful"}

# 3. Kiểm tra API root endpoint
curl http://localhost:8080/
# Expected: JSON response với db_host_from_env: "db", db_port_from_env: "5432"

# 4. Kiểm tra tasks endpoint
curl http://localhost:8080/tasks
# Expected: JSON array với sample tasks từ init.sql
```

### Bước 6: View Logs

```bash
# View logs của tất cả services
docker compose logs

# View logs của specific service
docker compose logs api
docker compose logs db

# Follow logs real-time
docker compose logs -f api
```

### Bước 7: Stop Services

```bash
# Stop và remove containers (giữ lại volumes)
docker compose down

# Stop và remove containers + volumes (xóa database data)
docker compose down -v
```

---

## Production Deployment

Hướng dẫn triển khai ứng dụng lên môi trường production với các best practices về security và reliability.

### 1. Environment Variables Configuration

**KHÔNG sử dụng giá trị mặc định cho production!** Tạo file `.env` với giá trị secure:

```bash
# Database Configuration - PRODUCTION VALUES
DB_HOST=db
DB_PORT=5432
DB_NAME=fullstack_prod
DB_USER=prod_user
DB_PASSWORD=<STRONG_RANDOM_PASSWORD>
```

**Cách tạo strong password:**

```bash
# Generate random password (Linux/Mac)
openssl rand -base64 32

# Hoặc sử dụng password manager như 1Password, LastPass
```

### 2. Secrets Management

**Best Practice:** Không lưu secrets trong plain text files!

#### Option 1: Docker Secrets (Docker Swarm)

```yaml
# docker-compose.prod.yml
services:
  api:
    secrets:
      - db_password
    environment:
      DB_PASSWORD_FILE: /run/secrets/db_password

secrets:
  db_password:
    external: true
```

#### Option 2: Environment Variables từ CI/CD

```bash
# Set environment variables trong CI/CD pipeline
export DB_PASSWORD="${VAULT_DB_PASSWORD}"
docker compose up -d
```

#### Option 3: External Secrets Manager

- **AWS Secrets Manager**
- **HashiCorp Vault**
- **Azure Key Vault**
- **Google Secret Manager**

### 3. Image Tags Best Practices

**KHÔNG sử dụng `latest` tag trong production!**

```yaml
# BAD - Không predictable
services:
  db:
    image: postgres:latest

# GOOD - Specific version
services:
  db:
    image: postgres:16-alpine
```

**Đối với custom images:**

```bash
# Tag image với version number
docker build -t myapp:1.2.3 ./api

# Push to registry
docker tag myapp:1.2.3 registry.example.com/myapp:1.2.3
docker push registry.example.com/myapp:1.2.3
```

### 4. Resource Limits

Giới hạn resources để tránh container tiêu thụ quá nhiều system resources:

```yaml
# docker-compose.prod.yml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: "1.0"
          memory: 512M
        reservations:
          cpus: "0.5"
          memory: 256M

  db:
    deploy:
      resources:
        limits:
          cpus: "2.0"
          memory: 2G
        reservations:
          cpus: "1.0"
          memory: 1G
```

### 5. Vulnerability Scanning

Scan images trước khi deploy:

```bash
# Sử dụng Docker Scout
docker scout cves postgres:16-alpine

# Sử dụng Trivy
trivy image postgres:16-alpine

# Sử dụng Snyk
snyk container test postgres:16-alpine
```

### 6. Production Deployment Steps

```bash
# 1. Pull latest code
git pull origin main

# 2. Build images với production tag
docker compose -f docker-compose.yml -f docker-compose.prod.yml build

# 3. Run vulnerability scan
docker scout cves docker-topic5-api:latest

# 4. Stop old containers
docker compose down

# 5. Start new containers
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 6. Verify deployment (xem phần Health Checks)
```

### 7. Database Backup

**Backup trước khi deploy:**

```bash
# Backup database
docker compose exec db pg_dump -U fullstack_user fullstack_demo > backup_$(date +%Y%m%d_%H%M%S).sql

# Verify backup file
ls -lh backup_*.sql
```

**Restore từ backup:**

```bash
# Restore database
docker compose exec -T db psql -U fullstack_user fullstack_demo < backup_20240101_120000.sql
```

---

## Health Checks

Hướng dẫn verify services hoạt động đúng sau deployment.

### 1. Container Health Status

```bash
# Kiểm tra status của tất cả containers
docker compose ps

# Expected output:
# NAME         STATUS
# topic5_api   Up
# topic5_db    Up (healthy)
```

**Giải thích health check của database:**

```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U fullstack_user -d fullstack_demo"]
  interval: 5s
  timeout: 3s
  retries: 10
```

- `pg_isready`: PostgreSQL utility kiểm tra database có sẵn sàng nhận connections
- `interval: 5s`: Chạy health check mỗi 5 giây
- `timeout: 3s`: Timeout sau 3 giây nếu không response
- `retries: 10`: Retry 10 lần trước khi mark là unhealthy

### 2. API Health Endpoint

```bash
# Kiểm tra API health
curl -f http://localhost:8080/health || echo "API is DOWN"

# Expected: {"status": "ok"}
# Exit code: 0 (success)
```

### 3. Database Connectivity Check

```bash
# Kiểm tra API có connect được database không
curl http://localhost:8080/db-check

# Expected: {"database": "connected", "message": "Database connection successful"}
```

### 4. End-to-End Functional Test

```bash
# Test CRUD operations
# 1. Create task
curl -X POST http://localhost:8080/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "Health check task"}'

# Expected: {"id": <new_id>, "title": "Health check task"}

# 2. Get all tasks
curl http://localhost:8080/tasks

# Expected: JSON array chứa task vừa tạo
```

### 5. Automated Health Check Script

Tạo script `health_check.sh`:

```bash
#!/bin/bash

echo "=== Health Check Started ==="

# Check API health
if curl -f -s http://localhost:8080/health > /dev/null; then
    echo "✓ API health: OK"
else
    echo "✗ API health: FAILED"
    exit 1
fi

# Check database connectivity
if curl -f -s http://localhost:8080/db-check > /dev/null; then
    echo "✓ Database connectivity: OK"
else
    echo "✗ Database connectivity: FAILED"
    exit 1
fi

# Check tasks endpoint
if curl -f -s http://localhost:8080/tasks > /dev/null; then
    echo "✓ Tasks endpoint: OK"
else
    echo "✗ Tasks endpoint: FAILED"
    exit 1
fi

echo "=== Health Check Passed ==="
```

**Sử dụng:**

```bash
chmod +x health_check.sh
./health_check.sh
```

---

## Monitoring và Logging

Best practices cho monitoring và logging trong production.

### 1. Container Logs

```bash
# View logs với timestamps
docker compose logs -t

# View logs của specific service
docker compose logs -t api

# Follow logs real-time
docker compose logs -f -t api

# View last 100 lines
docker compose logs --tail=100 api
```

### 2. Log Aggregation

**Option 1: Docker Logging Driver**

```yaml
# docker-compose.prod.yml
services:
  api:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

**Option 2: Centralized Logging (ELK Stack)**

```yaml
services:
  api:
    logging:
      driver: "gelf"
      options:
        gelf-address: "udp://logstash:12201"
        tag: "api"
```

**Option 3: Cloud Logging**

- **AWS CloudWatch Logs**
- **Google Cloud Logging**
- **Azure Monitor**

### 3. Metrics Collection

**Prometheus + Grafana Setup:**

```yaml
# docker-compose.monitoring.yml
services:
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

### 4. Container Stats

```bash
# View real-time resource usage
docker stats topic5_api topic5_db

# Expected output:
# CONTAINER    CPU %    MEM USAGE / LIMIT    MEM %    NET I/O
# topic5_api   0.50%    50MiB / 512MiB      9.77%    1.2kB / 850B
# topic5_db    1.20%    100MiB / 2GiB       4.88%    850B / 1.2kB
```

### 5. Alerting

**Setup alerts cho critical events:**

- Container restart
- High memory usage (>80%)
- High CPU usage (>80%)
- Database connection failures
- API response time > 1s

**Example: Prometheus Alert Rules**

```yaml
# alerts.yml
groups:
  - name: docker_alerts
    rules:
      - alert: ContainerDown
        expr: up{job="docker"} == 0
        for: 1m
        annotations:
          summary: "Container {{ $labels.instance }} is down"

      - alert: HighMemoryUsage
        expr: container_memory_usage_bytes / container_spec_memory_limit_bytes > 0.8
        for: 5m
        annotations:
          summary: "Container {{ $labels.name }} memory usage > 80%"
```

---

## Rollback Procedures

Hướng dẫn rollback về version trước khi deployment gặp vấn đề.

### 1. Quick Rollback (Same Host)

Nếu containers mới có vấn đề, rollback về containers cũ:

```bash
# 1. Stop containers hiện tại
docker compose down

# 2. Checkout code version trước
git log --oneline  # Xem commit history
git checkout <previous-commit-hash>

# 3. Rebuild và restart với code cũ
docker compose build
docker compose up -d

# 4. Verify rollback thành công
./health_check.sh
```

### 2. Rollback với Image Tags

Nếu sử dụng versioned images:

```bash
# 1. Stop containers hiện tại
docker compose down

# 2. Update docker-compose.yml với version cũ
# Thay vì: image: myapp:1.2.3
# Sử dụng: image: myapp:1.2.2

# 3. Pull image cũ và restart
docker compose pull
docker compose up -d

# 4. Verify rollback
./health_check.sh
```

### 3. Database Rollback

**Nếu database schema đã thay đổi:**

```bash
# 1. Stop API để tránh write operations
docker compose stop api

# 2. Restore database từ backup
docker compose exec -T db psql -U fullstack_user fullstack_demo < backup_before_deploy.sql

# 3. Restart API với code version cũ
git checkout <previous-commit-hash>
docker compose build api
docker compose up -d

# 4. Verify
./health_check.sh
```

### 4. Rollback Checklist

- [ ] Backup database trước khi rollback
- [ ] Document lý do rollback
- [ ] Notify team về rollback
- [ ] Stop API trước khi restore database
- [ ] Verify health checks sau rollback
- [ ] Check logs để confirm không có errors
- [ ] Update incident report

### 5. Prevention Strategies

**Để giảm thiểu nhu cầu rollback:**

1. **Blue-Green Deployment:** Chạy 2 environments song song
2. **Canary Deployment:** Deploy cho subset của users trước
3. **Feature Flags:** Enable/disable features không cần deploy
4. **Automated Testing:** Run tests trước khi deploy
5. **Staging Environment:** Test trên staging trước production

---

## Security Best Practices

Các best practices để đảm bảo security cho production deployment.

### 1. Change Default Passwords

**CRITICAL:** Không bao giờ sử dụng default passwords trong production!

```bash
# BAD - Default password
DB_PASSWORD=fullstack_pass

# GOOD - Strong random password
DB_PASSWORD=X9k2$mP7nQ4@vL8wR3zT6yU1hJ5bN0cF
```

**Password Requirements:**

- Minimum 16 characters
- Mix of uppercase, lowercase, numbers, special characters
- Không sử dụng dictionary words
- Unique cho mỗi environment

### 2. Secrets Management

**KHÔNG commit secrets vào Git!**

```bash
# Add to .gitignore
echo ".env" >> .gitignore
echo "*.sql" >> .gitignore  # Backup files có thể chứa sensitive data
```

**Sử dụng secrets management tools:**

```bash
# Example: HashiCorp Vault
vault kv put secret/myapp/db password="$DB_PASSWORD"

# Retrieve trong deployment script
export DB_PASSWORD=$(vault kv get -field=password secret/myapp/db)
```

### 3. Use Specific Image Tags

**KHÔNG sử dụng `latest` tag:**

```yaml
# BAD - Không predictable, có thể pull vulnerable version
services:
  db:
    image: postgres:latest

# GOOD - Specific version, reproducible
services:
  db:
    image: postgres:16.1-alpine  # Specific minor version
```

**Benefits:**

- Reproducible builds
- Easier rollback
- Avoid unexpected breaking changes
- Security audit trail

### 4. Vulnerability Scanning

**Scan images thường xuyên:**

```bash
# Scan base image
docker scout cves postgres:16-alpine

# Scan custom image
docker scout cves docker-topic5-api:latest

# Automated scanning trong CI/CD
# .github/workflows/security.yml
- name: Scan image
  run: |
    docker scout cves ${{ env.IMAGE_NAME }}:${{ env.VERSION }}
```

**Setup automated scanning:**

- Scan mỗi khi build image mới
- Scan scheduled (daily/weekly) cho running images
- Block deployment nếu có critical vulnerabilities

### 5. Resource Limits

**Prevent DoS attacks và resource exhaustion:**

```yaml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: "1.0" # Max 1 CPU core
          memory: 512M # Max 512MB RAM
        reservations:
          cpus: "0.5" # Guaranteed 0.5 CPU
          memory: 256M # Guaranteed 256MB RAM
```

**Benefits:**

- Prevent single container từ consuming tất cả resources
- Predictable performance
- Better resource allocation
- Protection against memory leaks

### 6. Run as Non-Root User

**Best practice: Không run containers as root:**

```dockerfile
# api/Dockerfile
FROM python:3.12-slim

# Create non-root user
RUN useradd -m -u 1000 appuser

# Set ownership
WORKDIR /app
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

CMD ["python", "app.py"]
```

**Benefits:**

- Limit damage nếu container bị compromise
- Follow principle of least privilege
- Compliance với security standards

### 7. Network Security

**Restrict network access:**

```yaml
services:
  api:
    networks:
      - frontend
      - backend

  db:
    networks:
      - backend # Database KHÔNG expose ra frontend network

networks:
  frontend:
  backend:
    internal: true # Không có external access
```

### 8. Read-Only Filesystem

**Mount volumes as read-only khi có thể:**

```yaml
services:
  api:
    volumes:
      - ./config:/app/config:ro # Read-only config

  db:
    volumes:
      - ./db/init.sql:/docker-entrypoint-initdb.d/init.sql:ro # Read-only init script
```

### 9. Security Scanning Checklist

- [ ] Change all default passwords
- [ ] Use secrets management tool
- [ ] Use specific image tags (not `latest`)
- [ ] Scan images for vulnerabilities
- [ ] Set resource limits
- [ ] Run containers as non-root user
- [ ] Restrict network access
- [ ] Use read-only volumes where possible
- [ ] Enable Docker Content Trust
- [ ] Regular security updates
- [ ] Monitor security advisories
- [ ] Implement least privilege access

### 10. Compliance và Auditing

**Enable audit logging:**

```bash
# Docker daemon audit logging
# /etc/docker/daemon.json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

**Regular security audits:**

- Review access logs monthly
- Audit user permissions quarterly
- Update dependencies regularly
- Review security policies annually

---

## Tổng Kết

Tài liệu này cung cấp hướng dẫn đầy đủ để deploy Docker Topic 5 application từ local development đến production environment. Các điểm chính cần nhớ:

1. **Local Development:** Sử dụng default values, focus vào functionality
2. **Production Deployment:** Prioritize security, reliability, và monitoring
3. **Health Checks:** Verify services hoạt động đúng sau mỗi deployment
4. **Monitoring:** Setup logging và metrics để detect issues sớm
5. **Rollback:** Có plan để rollback nhanh chóng khi cần
6. **Security:** Follow best practices để protect application và data

Để biết thêm chi tiết về project structure và usage instructions, xem [README.md](./README.md).
