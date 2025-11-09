# LLM Dungeon Master - Deployment Guide

Complete guide for deploying the LLM Dungeon Master application in various environments.

## Deployment Options

### 1. Docker (Recommended) ⭐

**Best for**: Production deployment, team development, easy scaling

**Pros**:
- Consistent environment across systems
- Easy to deploy and manage
- Includes PostgreSQL and Redis
- Simple backup/restore

**See**: [Docker Deployment Guide](./DOCKER.md)

### 2. Local Development

**Best for**: Solo development, testing, no Docker available

**Pros**:
- Simple setup
- Direct access to code
- Uses SQLite (no database server needed)

**See**: [Local Setup](#local-development-setup)

### 3. Cloud Deployment

**Best for**: Public hosting, high availability

**Pros**:
- Managed infrastructure
- Auto-scaling
- High availability

**See**: [Cloud Deployment](#cloud-deployment)

---

## Local Development Setup

### Prerequisites

- Python 3.12 or later
- UV package manager
- Git

### Installation

#### 1. Install UV

**macOS/Linux**:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows**:
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

#### 2. Clone Repository

```bash
git clone <repository-url>
cd DNDGame-Retro
```

#### 3. Create Virtual Environment

```bash
uv venv
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\activate  # Windows
```

#### 4. Install Dependencies

```bash
uv pip install -e .
```

#### 5. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and set your OpenAI API key:
```bash
OPENAI_API_KEY=sk-your-api-key-here
LLM_PROVIDER=openai
LLM_MODEL=gpt-4

# For local development, SQLite is sufficient
DATABASE_URL=sqlite:///./data/dndgame.db
```

#### 6. Run the Server

```bash
rpg serve
```

The API will be available at: http://localhost:8000

#### 7. Play the Game

In a new terminal:
```bash
source .venv/bin/activate
rpg play
```

### Development Commands

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=src/llm_dungeon_master

# Format code
ruff format .

# Lint code
ruff check .

# Type check
mypy src/
```

---

## Docker Deployment

See [DOCKER.md](./DOCKER.md) for complete Docker deployment guide.

### Quick Start

```bash
# Configure environment
cp .env.example .env
# Edit .env with your settings

# Start development mode
./scripts/docker/start-dev.sh

# Or start production mode
./scripts/docker/start-prod.sh
```

---

## Cloud Deployment

### AWS Deployment

#### Using ECS (Elastic Container Service)

1. **Build and Push Image**:
```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Build image
docker build -t rpg-dungeon-master:latest -f Dockerfile --target production .

# Tag image
docker tag rpg-dungeon-master:latest \
  <account-id>.dkr.ecr.us-east-1.amazonaws.com/rpg-dungeon-master:latest

# Push image
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/rpg-dungeon-master:latest
```

2. **Create ECS Task Definition**:
```json
{
  "family": "rpg-dungeon-master",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [
    {
      "name": "api",
      "image": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/rpg-dungeon-master:latest",
      "portMappings": [{"containerPort": 8000}],
      "environment": [
        {"name": "DATABASE_URL", "value": "postgresql://..."},
        {"name": "REDIS_URL", "value": "redis://..."}
      ],
      "secrets": [
        {
          "name": "OPENAI_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:..."
        }
      ],
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
        "interval": 30,
        "timeout": 10,
        "retries": 3
      }
    }
  ]
}
```

3. **Set Up RDS (PostgreSQL)**:
```bash
aws rds create-db-instance \
  --db-instance-identifier rpg-dungeon-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --master-username rpguser \
  --master-user-password <strong-password> \
  --allocated-storage 20
```

4. **Set Up ElastiCache (Redis)**:
```bash
aws elasticache create-cache-cluster \
  --cache-cluster-id rpg-redis \
  --cache-node-type cache.t3.micro \
  --engine redis \
  --num-cache-nodes 1
```

### Google Cloud Run

1. **Build and Push**:
```bash
# Set project
gcloud config set project <project-id>

# Build
gcloud builds submit --tag gcr.io/<project-id>/rpg-dungeon-master

# Or use Cloud Build
gcloud builds submit --config cloudbuild.yaml
```

2. **Deploy**:
```bash
gcloud run deploy rpg-dungeon-master \
  --image gcr.io/<project-id>/rpg-dungeon-master \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="DATABASE_URL=postgresql://...,REDIS_URL=redis://..." \
  --set-secrets="OPENAI_API_KEY=openai-key:latest" \
  --memory 1Gi \
  --cpu 1
```

3. **Set Up Cloud SQL (PostgreSQL)**:
```bash
gcloud sql instances create rpg-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-central1
```

### Azure Container Instances

1. **Build and Push to ACR**:
```bash
# Login
az acr login --name <registry-name>

# Build and push
az acr build --registry <registry-name> --image rpg-dungeon-master:latest .
```

2. **Deploy**:
```bash
az container create \
  --resource-group rpg-dungeon-rg \
  --name rpg-api \
  --image <registry-name>.azurecr.io/rpg-dungeon-master:latest \
  --cpu 1 \
  --memory 1 \
  --ports 8000 \
  --environment-variables \
    DATABASE_URL="postgresql://..." \
    REDIS_URL="redis://..." \
  --secure-environment-variables \
    OPENAI_API_KEY="<key>"
```

---

## Environment Variables Reference

### Required

| Variable | Description | Example |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | `sk-...` |
| `DATABASE_URL` | Database connection URL | `postgresql://user:pass@host:5432/db` |

### Optional

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `openai` | LLM provider (`openai`, `anthropic`, `mock`) |
| `LLM_MODEL` | `gpt-4-turbo-preview` | Model name |
| `REDIS_URL` | `` | Redis connection URL |
| `SERVER_HOST` | `0.0.0.0` | Server bind address |
| `SERVER_PORT` | `8000` | Server port |
| `DEBUG` | `true` | Debug mode |
| `LOG_LEVEL` | `INFO` | Logging level |
| `LOG_FORMAT` | `pretty` | Log format (`json` or `pretty`) |
| `RATE_LIMIT_ENABLED` | `true` | Enable rate limiting |
| `RATE_LIMIT_PER_MINUTE` | `60` | Max requests per minute |
| `CORS_ORIGINS` | `http://localhost:3000,...` | Allowed CORS origins |
| `SECRET_KEY` | (random) | Session secret key |

---

## Monitoring and Logging

### Health Checks

The application provides three health check endpoints:

1. **`/health`** - Comprehensive health check
   - Checks database connectivity
   - Checks LLM provider configuration
   - Returns detailed status

2. **`/ready`** - Readiness probe (for Kubernetes)
   - Returns 200 if service is ready to accept traffic
   - Returns 503 if not ready

3. **`/live`** - Liveness probe (for Kubernetes)
   - Returns 200 if application is running
   - Always returns success unless crashed

### Logging

**Development** (`LOG_FORMAT=pretty`):
- Colorized console output
- Human-readable format
- Includes stack traces

**Production** (`LOG_FORMAT=json`):
- Structured JSON logs
- Machine-parseable
- Easy to aggregate (Elasticsearch, Splunk, etc.)

**Example JSON Log**:
```json
{
  "timestamp": "2025-11-08T14:30:22.123Z",
  "level": "info",
  "logger": "api",
  "event": "api_request",
  "method": "POST",
  "path": "/api/sessions/1/messages",
  "status_code": 200,
  "duration_ms": 45.2,
  "session_id": 1
}
```

### Metrics

Enable metrics with `ENABLE_METRICS=true`.

Access metrics at `/metrics` (Prometheus format).

---

## Security Checklist

Before deploying to production:

- [ ] Change all default passwords
- [ ] Generate secure `SECRET_KEY` (use `openssl rand -hex 32`)
- [ ] Set `DEBUG=false`
- [ ] Configure proper `CORS_ORIGINS`
- [ ] Enable rate limiting (`RATE_LIMIT_ENABLED=true`)
- [ ] Use HTTPS (SSL/TLS via reverse proxy)
- [ ] Restrict database access (firewall, VPC)
- [ ] Use secrets manager for sensitive data
- [ ] Enable audit logging
- [ ] Set up monitoring and alerts
- [ ] Configure automated backups
- [ ] Review and harden container security
- [ ] Implement log aggregation
- [ ] Set up intrusion detection
- [ ] Configure web application firewall (WAF)

---

## Performance Tuning

### Database

**Connection Pooling**:
```python
# In production, increase pool size
DATABASE_URL=postgresql://user:pass@host:5432/db?pool_size=20&max_overflow=10
```

**Indexes**:
- All foreign keys are indexed
- Add custom indexes for frequent queries

### Redis Caching

Enable Redis for session caching:
```bash
REDIS_URL=redis://:password@host:6379/0
```

### Uvicorn Workers

Increase workers for production:
```bash
# In Dockerfile CMD
CMD ["uvicorn", "llm_dungeon_master.server:app", "--host", "0.0.0.0", "--workers", "4"]
```

Formula: `workers = (2 * CPU_cores) + 1`

### Rate Limiting

Adjust rate limits based on usage:
```bash
RATE_LIMIT_PER_MINUTE=120  # Higher for production
RATE_LIMIT_BURST=20
```

---

## Backup and Recovery

### Automated Backups (Docker)

```bash
# Add to cron (daily at 2 AM)
0 2 * * * cd /path/to/DNDGame-Retro && ./scripts/docker/backup.sh
```

### Manual Backup

```bash
./scripts/docker/backup.sh
```

### Restore from Backup

```bash
./scripts/docker/restore.sh ./backups/rpg_backup_20251108_143022.tar.gz
```

### Cloud Backups

**AWS RDS**: Enable automated backups (7-35 days retention)
**Google Cloud SQL**: Enable automated backups
**Azure Database**: Enable geo-redundant backups

---

## Scaling

### Horizontal Scaling

1. **Load Balancer**: Nginx, HAProxy, or cloud load balancer
2. **Multiple API Instances**: Run multiple containers
3. **Shared Database**: PostgreSQL with connection pooling
4. **Shared Cache**: Redis cluster
5. **Session Affinity**: Use Redis for session storage

### Vertical Scaling

Increase container resources:
```yaml
# docker-compose.yml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

---

## Troubleshooting

See [DOCKER.md#troubleshooting](./DOCKER.md#troubleshooting) for common issues.

### General Issues

**Can't connect to database**:
- Verify `DATABASE_URL` is correct
- Check database is running
- Check network connectivity
- Verify credentials

**LLM API errors**:
- Verify `OPENAI_API_KEY` is valid
- Check API quota and billing
- Check network connectivity
- Try with `LLM_PROVIDER=mock` for testing

**Performance issues**:
- Check `docker stats` for resource usage
- Increase workers/resources
- Enable Redis caching
- Optimize database queries

---

## Support

- **Documentation**: Check `/docs` folder
- **API Reference**: http://localhost:8000/docs
- **GitHub Issues**: Report bugs and feature requests
- **Logs**: Check `./logs/rpg_dungeon.log`

---

## Next Steps

- [Docker Guide](./DOCKER.md) - Docker deployment details
- [Player's Guide](./PLAYER_GUIDE.md) - How to play
- [DM's Guide](./DM_GUIDE.md) - How to run games
- [Commands Reference](./COMMANDS.md) - CLI commands
