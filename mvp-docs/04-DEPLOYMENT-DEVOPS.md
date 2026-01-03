# Deployment & DevOps Guide

## Overview

This document covers the complete deployment lifecycle for the Video Intelligence Platform, from local development through production deployment on Jetson devices.

---

## Repository Structure

```
video-intelligence/
├── .github/
│   └── workflows/
│       ├── build.yml           # CI: lint, test, build
│       ├── deploy.yml          # CD: push to registry
│       └── test-jetson.yml     # Hardware tests
├── docker/
│   ├── Dockerfile              # Main application
│   ├── Dockerfile.dev          # Development with hot-reload
│   └── docker-compose.yml      # Full stack
├── src/
│   ├── api/                    # FastAPI routes
│   ├── services/               # Business logic
│   ├── tasks/                  # Celery tasks
│   ├── models/                 # Data models
│   ├── core/                   # Config, DB, utils
│   └── main.py                 # Entry point
├── frontend/
│   ├── src/                    # React application
│   ├── package.json
│   └── vite.config.ts
├── tests/
│   ├── unit/                   # Unit tests
│   ├── integration/            # Integration tests
│   └── e2e/                    # End-to-end tests
├── scripts/
│   ├── setup-jetson.sh         # Device provisioning
│   ├── benchmark.py            # Performance testing
│   └── export-models.py        # TensorRT export
├── config/
│   ├── default.yaml            # Default configuration
│   └── production.yaml         # Production overrides
├── requirements.txt            # Python dependencies
├── requirements-dev.txt        # Dev dependencies
└── README.md
```

---

## Development Environment

### Prerequisites

| Component | Version | Notes |
|-----------|---------|-------|
| Python | 3.10+ | Match Jetson JetPack |
| Node.js | 18+ | Frontend build |
| Docker | 24+ | Container runtime |
| Git | 2.40+ | Version control |

### Local Setup (x86 Development Machine)

```bash
# Clone repository
git clone https://github.com/myorg/video-intelligence.git
cd video-intelligence

# Create Python virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install frontend dependencies
cd frontend
npm install
cd ..

# Start development services
docker-compose -f docker/docker-compose.dev.yml up -d redis postgres

# Run API server (with hot-reload)
uvicorn src.main:app --reload --host 0.0.0.0 --port 8080

# In another terminal, run frontend
cd frontend
npm run dev
```

### Development Docker Compose

```yaml
# docker/docker-compose.dev.yml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  postgres:
    image: postgres:16-alpine
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: video_intel
      POSTGRES_PASSWORD: devpassword
      POSTGRES_DB: video_intelligence
    volumes:
      - postgres_data:/var/lib/postgresql/data

  chromadb:
    image: chromadb/chroma:latest
    ports:
      - "8000:8000"
    volumes:
      - chroma_data:/chroma/chroma

volumes:
  redis_data:
  postgres_data:
  chroma_data:
```

### VS Code Configuration

```json
// .vscode/settings.json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "none",
  "[python]": {
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports": true
    },
    "editor.defaultFormatter": "charliermarsh.ruff"
  }
}
```

---

## Docker Configuration

### Production Dockerfile

```dockerfile
# docker/Dockerfile
# Build stage for frontend
FROM node:18-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Main application
FROM dustynv/nano_llm:r36.4.0

# Set environment
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libgl1-mesa-glx \
    libglib2.0-0 \
    postgresql-client \
    nginx \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY config/ ./config/
COPY scripts/ ./scripts/

# Copy built frontend
COPY --from=frontend-builder /app/frontend/dist /var/www/frontend

# Copy nginx config
COPY docker/nginx.conf /etc/nginx/nginx.conf

# Create data directories
RUN mkdir -p /data/videos /data/models /data/chroma

# Expose ports
EXPOSE 80 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Entrypoint
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
```

### Entrypoint Script

```bash
#!/bin/bash
# docker/entrypoint.sh

set -e

echo "Starting Video Intelligence Platform..."

# Wait for dependencies
echo "Waiting for Redis..."
until redis-cli -h ${REDIS_HOST:-redis} ping > /dev/null 2>&1; do
    sleep 1
done

echo "Waiting for PostgreSQL..."
until pg_isready -h ${POSTGRES_HOST:-postgres} -U ${POSTGRES_USER:-video_intel} > /dev/null 2>&1; do
    sleep 1
done

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Start services based on role
ROLE=${ROLE:-all}

case $ROLE in
    api)
        echo "Starting API server..."
        exec uvicorn src.main:app --host 0.0.0.0 --port 8080
        ;;
    worker)
        echo "Starting Celery worker..."
        exec celery -A src.tasks worker --loglevel=info --queues=${QUEUES:-cpu,gpu}
        ;;
    all)
        echo "Starting all services..."
        # Start nginx in background
        nginx

        # Start Celery worker in background
        celery -A src.tasks worker --loglevel=info --queues=cpu,gpu &

        # Start API server (foreground)
        exec uvicorn src.main:app --host 0.0.0.0 --port 8080
        ;;
esac
```

### Production Docker Compose

```yaml
# docker/docker-compose.yml
version: '3.8'

services:
  app:
    build:
      context: ..
      dockerfile: docker/Dockerfile
    runtime: nvidia
    ports:
      - "80:80"
      - "8080:8080"
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
      - REDIS_HOST=redis
      - POSTGRES_HOST=postgres
      - POSTGRES_USER=video_intel
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_DB=video_intelligence
      - MODEL_NAME=Efficient-Large-Model/VILA1.5-7b
    volumes:
      - video_data:/data/videos
      - model_data:/data/models
      - chroma_data:/data/chroma
    depends_on:
      - redis
      - postgres
    deploy:
      resources:
        reservations:
          devices:
            - capabilities: [gpu]

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: video_intel
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: video_intelligence
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  video_data:
  model_data:
  chroma_data:
  redis_data:
  postgres_data:
```

---

## CI/CD Pipeline

### GitHub Actions: Build & Test

```yaml
# .github/workflows/build.yml
name: Build & Test

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  PYTHON_VERSION: "3.10"
  NODE_VERSION: "18"

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Install dependencies
        run: |
          pip install ruff mypy
          pip install -r requirements.txt

      - name: Lint with ruff
        run: ruff check src/

      - name: Type check with mypy
        run: mypy src/ --ignore-missing-imports

  test-unit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Run unit tests
        run: pytest tests/unit/ -v --cov=src --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: coverage.xml

  test-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Node
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: Install dependencies
        run: |
          cd frontend
          npm ci

      - name: Lint
        run: |
          cd frontend
          npm run lint

      - name: Build
        run: |
          cd frontend
          npm run build

  build-image:
    needs: [lint, test-unit, test-frontend]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Set up QEMU
        uses: docker/setup-qemu-action@v3

      - name: Login to Container Registry
        if: github.event_name != 'pull_request'
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          file: docker/Dockerfile
          platforms: linux/arm64
          push: ${{ github.event_name != 'pull_request' }}
          tags: |
            ghcr.io/${{ github.repository }}:${{ github.sha }}
            ghcr.io/${{ github.repository }}:latest
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

### GitHub Actions: Deploy

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    tags:
      - 'v*'
  workflow_dispatch:
    inputs:
      environment:
        description: 'Deployment environment'
        required: true
        default: 'staging'
        type: choice
        options:
          - staging
          - production

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: ${{ github.event.inputs.environment || 'production' }}
    steps:
      - uses: actions/checkout@v4

      - name: Login to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Deploy to Jetson
        uses: appleboy/ssh-action@v1.0.0
        with:
          host: ${{ secrets.JETSON_HOST }}
          username: ${{ secrets.JETSON_USER }}
          key: ${{ secrets.JETSON_SSH_KEY }}
          script: |
            cd /opt/video-intelligence

            # Pull latest image
            docker pull ghcr.io/${{ github.repository }}:${{ github.sha }}

            # Tag as current
            docker tag ghcr.io/${{ github.repository }}:${{ github.sha }} video-intelligence:current

            # Restart services
            docker-compose down
            docker-compose up -d

            # Verify health
            sleep 30
            curl -f http://localhost:8080/health || exit 1

            echo "Deployment successful!"
```

### GitHub Actions: Jetson Hardware Tests

```yaml
# .github/workflows/test-jetson.yml
name: Jetson Hardware Tests

on:
  push:
    branches: [main]
  schedule:
    - cron: '0 6 * * *'  # Daily at 6 AM

jobs:
  test-jetson:
    runs-on: self-hosted  # Jetson device as runner
    steps:
      - uses: actions/checkout@v4

      - name: Pull latest image
        run: |
          docker pull ghcr.io/${{ github.repository }}:latest

      - name: Run integration tests
        run: |
          docker run --rm --runtime nvidia \
            -v $(pwd)/tests:/tests \
            ghcr.io/${{ github.repository }}:latest \
            pytest /tests/integration/ -v --jetson

      - name: Run benchmarks
        run: |
          docker run --rm --runtime nvidia \
            ghcr.io/${{ github.repository }}:latest \
            python scripts/benchmark.py --output /tmp/benchmark.json

      - name: Upload benchmark results
        uses: actions/upload-artifact@v4
        with:
          name: benchmark-results
          path: /tmp/benchmark.json
```

---

## Jetson Device Setup

### Initial Provisioning

```bash
#!/bin/bash
# scripts/setup-jetson.sh

set -e

echo "=== Jetson Device Setup ==="

# 1. System updates
echo "Updating system..."
sudo apt update && sudo apt upgrade -y

# 2. Set max performance mode
echo "Setting performance mode..."
sudo nvpmodel -m 0
sudo jetson_clocks

# 3. Install Docker (if not present)
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
fi

# 4. Configure NVIDIA Container Runtime
echo "Configuring NVIDIA runtime..."
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

# 5. Create application directories
echo "Creating directories..."
sudo mkdir -p /opt/video-intelligence
sudo mkdir -p /data/{videos,models,chroma}
sudo chown -R $USER:$USER /opt/video-intelligence /data

# 6. Install docker-compose
echo "Installing docker-compose..."
sudo pip3 install docker-compose

# 7. Configure swap (optional, for larger models)
echo "Configuring swap..."
sudo fallocate -l 16G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# 8. Set up systemd service
echo "Creating systemd service..."
sudo tee /etc/systemd/system/video-intelligence.service << EOF
[Unit]
Description=Video Intelligence Platform
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/video-intelligence
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
User=$USER

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable video-intelligence

echo "=== Setup Complete ==="
echo "Reboot recommended. Then run: docker-compose up -d"
```

### First Deployment

```bash
# On Jetson device
cd /opt/video-intelligence

# Copy docker-compose.yml
scp user@build-server:video-intelligence/docker/docker-compose.yml .

# Create environment file
cat > .env << EOF
POSTGRES_PASSWORD=$(openssl rand -base64 32)
EOF

# Pull images
docker-compose pull

# Start services
docker-compose up -d

# Check logs
docker-compose logs -f

# Verify health
curl http://localhost:8080/health
```

---

## OTA Updates

### Pull-Based Updates (Simple)

```bash
#!/bin/bash
# scripts/update.sh

set -e

cd /opt/video-intelligence

echo "Checking for updates..."

# Pull latest image
docker-compose pull

# Check if image changed
CURRENT=$(docker inspect --format='{{.Id}}' video-intelligence:current 2>/dev/null || echo "none")
LATEST=$(docker inspect --format='{{.Id}}' ghcr.io/myorg/video-intelligence:latest)

if [ "$CURRENT" != "$LATEST" ]; then
    echo "New version available, updating..."

    # Tag current as backup
    docker tag video-intelligence:current video-intelligence:backup 2>/dev/null || true

    # Tag new as current
    docker tag ghcr.io/myorg/video-intelligence:latest video-intelligence:current

    # Restart with new image
    docker-compose down
    docker-compose up -d

    # Verify health
    sleep 30
    if curl -sf http://localhost:8080/health > /dev/null; then
        echo "Update successful!"
        docker rmi video-intelligence:backup 2>/dev/null || true
    else
        echo "Health check failed, rolling back..."
        docker tag video-intelligence:backup video-intelligence:current
        docker-compose down
        docker-compose up -d
        exit 1
    fi
else
    echo "Already up to date."
fi
```

### Cron-Based Auto-Updates

```bash
# Add to crontab: crontab -e
# Check for updates daily at 3 AM
0 3 * * * /opt/video-intelligence/scripts/update.sh >> /var/log/video-intelligence-update.log 2>&1
```

---

## Monitoring & Logging

### Health Endpoint

```python
# src/api/health.py
from fastapi import APIRouter
import psutil
import subprocess

router = APIRouter()

@router.get("/health")
async def health():
    # GPU info
    gpu_info = get_gpu_info()

    return {
        "status": "healthy",
        "version": os.getenv("APP_VERSION", "dev"),
        "uptime_seconds": get_uptime(),
        "gpu": {
            "memory_used_mb": gpu_info["memory_used"],
            "memory_total_mb": gpu_info["memory_total"],
            "temperature_c": gpu_info["temperature"],
        },
        "cpu": {
            "percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
        },
        "services": {
            "redis": check_redis(),
            "postgres": check_postgres(),
            "vlm_loaded": check_vlm(),
        },
        "stats": {
            "videos_indexed": get_video_count(),
            "total_frames": get_frame_count(),
        }
    }

def get_gpu_info():
    result = subprocess.run(
        ["tegrastats", "--interval", "100", "--count", "1"],
        capture_output=True, text=True
    )
    # Parse tegrastats output
    ...
```

### Logging Configuration

```python
# src/core/logging.py
import logging
import sys
from pythonjsonlogger import jsonlogger

def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # JSON formatter for structured logging
    handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Reduce noise from libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
```

### Log Aggregation (Optional)

```yaml
# docker-compose with logging
services:
  app:
    logging:
      driver: "json-file"
      options:
        max-size: "100m"
        max-file: "3"
        labels: "service"

  # Optional: Promtail for Loki
  promtail:
    image: grafana/promtail:latest
    volumes:
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
      - ./promtail-config.yml:/etc/promtail/config.yml
    command: -config.file=/etc/promtail/config.yml
```

---

## Backup & Recovery

### Backup Script

```bash
#!/bin/bash
# scripts/backup.sh

BACKUP_DIR="/backup/video-intelligence"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

echo "Backing up PostgreSQL..."
docker exec postgres pg_dump -U video_intel video_intelligence | gzip > $BACKUP_DIR/postgres_$DATE.sql.gz

echo "Backing up ChromaDB..."
tar -czf $BACKUP_DIR/chroma_$DATE.tar.gz /data/chroma

echo "Backing up configuration..."
cp /opt/video-intelligence/.env $BACKUP_DIR/env_$DATE

echo "Cleaning old backups (keep 7 days)..."
find $BACKUP_DIR -type f -mtime +7 -delete

echo "Backup complete: $BACKUP_DIR"
```

### Restore Script

```bash
#!/bin/bash
# scripts/restore.sh

BACKUP_DIR="/backup/video-intelligence"
BACKUP_DATE=$1

if [ -z "$BACKUP_DATE" ]; then
    echo "Usage: $0 <backup_date>"
    echo "Available backups:"
    ls $BACKUP_DIR/*.sql.gz | xargs -n1 basename | sed 's/postgres_//' | sed 's/.sql.gz//'
    exit 1
fi

echo "Restoring from backup: $BACKUP_DATE"

# Stop services
docker-compose down

# Restore PostgreSQL
echo "Restoring PostgreSQL..."
docker-compose up -d postgres
sleep 5
gunzip -c $BACKUP_DIR/postgres_$BACKUP_DATE.sql.gz | docker exec -i postgres psql -U video_intel video_intelligence

# Restore ChromaDB
echo "Restoring ChromaDB..."
rm -rf /data/chroma/*
tar -xzf $BACKUP_DIR/chroma_$BACKUP_DATE.tar.gz -C /

# Restart all services
docker-compose up -d

echo "Restore complete!"
```

---

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| GPU out of memory | Model too large | Use smaller model or reduce batch size |
| Container won't start | Missing NVIDIA runtime | Check `docker info` for nvidia runtime |
| Slow inference | Thermal throttling | Check `tegrastats`, improve cooling |
| Database connection error | PostgreSQL not ready | Check container logs, wait for startup |
| VLM returns garbage | Model loading failed | Check model files, re-download |

### Debug Commands

```bash
# Check GPU status
tegrastats

# Check container logs
docker-compose logs -f app

# Enter container shell
docker-compose exec app bash

# Check NVIDIA runtime
docker run --rm --runtime nvidia nvidia-smi

# Check disk space
df -h /data

# Check memory
free -h

# Test VLM loading
docker-compose exec app python -c "
from nano_llm import NanoLLM
model = NanoLLM.from_pretrained('Efficient-Large-Model/VILA1.5-7b')
print('VLM loaded successfully')
"
```

---

## Performance Tuning

### Jetson Power Mode

```bash
# Maximum performance (60W)
sudo nvpmodel -m 0
sudo jetson_clocks

# Check current mode
sudo nvpmodel -q
```

### TensorRT Engine Caching

```python
# Engines are cached after first load
# Location: /data/models/.cache/

# Pre-build engines during deployment
python scripts/export-models.py --warmup
```

### Memory Optimization

```yaml
# Environment variables for memory tuning
environment:
  - PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
  - CUDA_MODULE_LOADING=LAZY
```

---

*Deployment & DevOps Guide - January 2026*
