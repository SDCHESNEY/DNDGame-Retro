# Docker Deployment Guide

This guide covers deploying the LLM Dungeon Master using Docker and Docker Compose.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Services](#services)
- [Development Mode](#development-mode)
- [Production Mode](#production-mode)
- [Data Management](#data-management)
- [Troubleshooting](#troubleshooting)
- [Security](#security)

## Prerequisites

### Required Software

- **Docker**: Version 20.10 or later
- **Docker Compose**: Version 2.0 or later
- **Git**: For cloning the repository

### System Requirements

**Minimum**:
- 2GB RAM
- 10GB disk space
- 2 CPU cores

**Recommended**:
- 4GB RAM
- 20GB disk space
- 4 CPU cores

### Installation

**macOS**:
```bash
brew install docker docker-compose
```

**Linux (Ubuntu/Debian)**:
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo apt-get install docker-compose-plugin
```

**Windows**:
Download and install [Docker Desktop](https://www.docker.com/products/docker-desktop)

## Quick Start

### 1. Clone Repository

```bash
git clone <repository-url>
cd DNDGame-Retro
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and set your OpenAI API key:
```bash
OPENAI_API_KEY=sk-your-api-key-here
```

**Important**: Change default passwords for production:
```bash
POSTGRES_PASSWORD=your-strong-password
REDIS_PASSWORD=your-redis-password
SECRET_KEY=$(openssl rand -hex 32)
```

### 3. Start Services

**Development Mode** (with hot reload):
```bash
./scripts/docker/start-dev.sh
```

**Production Mode** (optimized):
```bash
./scripts/docker/start-prod.sh
```

### 4. Verify Deployment

```bash
# Check health
curl http://localhost:8000/health

# View API docs
open http://localhost:8000/docs

# Check logs
docker-compose logs -f api
```

## Configuration

### Environment Variables

The application is configured via environment variables in `.env`:

#### Database Settings

```bash
# PostgreSQL configuration
POSTGRES_DB=rpg_dungeon
POSTGRES_USER=rpguser
POSTGRES_PASSWORD=changeme_strong_password_here

# Database URL (auto-constructed for Docker)
DATABASE_URL=postgresql://rpguser:password@db:5432/rpg_dungeon
```

#### Redis Settings

```bash
REDIS_PASSWORD=changeme_redis_password_here
REDIS_URL=redis://:password@redis:6379/0
```

#### LLM Configuration

```bash
# OpenAI
OPENAI_API_KEY=sk-your-api-key-here
LLM_PROVIDER=openai
LLM_MODEL=gpt-4

# Alternative: Anthropic
# ANTHROPIC_API_KEY=your-key
# LLM_PROVIDER=anthropic
# LLM_MODEL=claude-3-opus-20240229
```

#### Server Configuration

```bash
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
DEBUG=true  # Set to false in production

# CORS (comma-separated origins)
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
```

#### Rate Limiting

```bash
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_BURST=10
```

#### Logging

```bash
LOG_LEVEL=INFO
LOG_FORMAT=json  # Options: json, pretty
LOG_FILE=/app/logs/rpg_dungeon.log
LOG_MAX_BYTES=10485760  # 10MB
LOG_BACKUP_COUNT=5
```

## Services

The Docker Compose stack includes three services:

### 1. PostgreSQL Database (`db`)

- **Image**: `postgres:15-alpine`
- **Port**: 5432
- **Volume**: `postgres_data` (persistent)
- **Health Check**: pg_isready

**Access Database**:
```bash
docker-compose exec db psql -U rpguser rpg_dungeon
```

### 2. Redis Cache (`redis`)

- **Image**: `redis:7-alpine`
- **Port**: 6379
- **Volume**: `redis_data` (persistent)
- **Health Check**: redis-cli ping

**Access Redis**:
```bash
docker-compose exec redis redis-cli
# AUTH <REDIS_PASSWORD>
```

### 3. FastAPI Server (`api` / `api-prod`)

- **Build**: Multi-stage Dockerfile
- **Port**: 8000
- **Volumes**: 
  - `./src:/app/src` (development only, hot reload)
  - `./logs:/app/logs` (persistent logs)
  - `app_data` (application data)
- **Health Check**: `/health` endpoint

## Development Mode

Development mode enables hot reload and debugging features.

### Start Development Environment

```bash
./scripts/docker/start-dev.sh
```

This starts:
- PostgreSQL database
- Redis cache
- FastAPI server with hot reload

### Features

- **Hot Reload**: Changes to `src/` are reflected immediately
- **Debug Mode**: Detailed error messages
- **Pretty Logging**: Colorized console output
- **Source Mapping**: Local `src/` mounted in container

### Development Workflow

1. **Make Changes**: Edit files in `src/llm_dungeon_master/`
2. **Auto Reload**: Server restarts automatically
3. **Test**: Use CLI or API
4. **Debug**: Check logs with `docker-compose logs -f api`

### Access Services

```bash
# API
curl http://localhost:8000/health

# Database
docker-compose exec db psql -U rpguser rpg_dungeon

# Redis
docker-compose exec redis redis-cli

# Shell in API container
./scripts/docker/shell.sh api

# View logs
./scripts/docker/logs.sh api
```

## Production Mode

Production mode is optimized for performance and security.

### Start Production Environment

```bash
./scripts/docker/start-prod.sh
```

### Features

- **Optimized Build**: Compiled bytecode, no source mapping
- **Security**: Non-root user, minimal attack surface
- **JSON Logging**: Structured logs for aggregation
- **Multiple Workers**: 4 uvicorn workers
- **No Debug**: Production-grade error handling

### Production Checklist

Before deploying to production:

- [ ] Change all default passwords in `.env`
- [ ] Generate secure `SECRET_KEY`
- [ ] Set `DEBUG=false`
- [ ] Configure proper `CORS_ORIGINS`
- [ ] Set up SSL/TLS (use reverse proxy like Nginx)
- [ ] Enable log aggregation
- [ ] Set up monitoring and alerts
- [ ] Configure backups
- [ ] Review security settings

### Recommended Architecture

```
Internet
    ↓
Nginx/Caddy (SSL/TLS, rate limiting)
    ↓
Docker Network
    ├── FastAPI (api-prod)
    ├── PostgreSQL (db)
    └── Redis (redis)
```

## Data Management

### Backup

Create a backup of all data:

```bash
./scripts/docker/backup.sh
```

This creates:
- PostgreSQL database dump
- Docker volume backup
- Combined archive in `./backups/`

### Restore

Restore from a backup:

```bash
./scripts/docker/restore.sh ./backups/rpg_backup_20251108_143022.tar.gz
```

**Warning**: This overwrites current data. You will be prompted to confirm.

### Manual Backup

**Database Only**:
```bash
docker-compose exec db pg_dump -U rpguser rpg_dungeon > backup.sql
```

**Restore Database**:
```bash
docker-compose exec -T db psql -U rpguser rpg_dungeon < backup.sql
```

### Volume Management

**List Volumes**:
```bash
docker volume ls | grep rpg_dungeon
```

**Inspect Volume**:
```bash
docker volume inspect rpg_dungeon_postgres_data
```

**Remove All Data** (destructive):
```bash
docker-compose down -v
```

## Troubleshooting

### Service Won't Start

**Check Status**:
```bash
docker-compose ps
```

**Check Logs**:
```bash
docker-compose logs api
docker-compose logs db
docker-compose logs redis
```

**Common Issues**:

1. **Port Already in Use**:
   ```bash
   # Find process using port 8000
   lsof -i :8000
   # Kill it or change PORT in .env
   ```

2. **Database Connection Failed**:
   ```bash
   # Check database is running
   docker-compose ps db
   # Check database logs
   docker-compose logs db
   # Verify credentials in .env
   ```

3. **Health Check Failing**:
   ```bash
   # Check health endpoint directly
   curl http://localhost:8000/health
   # Check container health
   docker inspect rpg_api | grep -A 10 Health
   ```

### Performance Issues

**Check Resource Usage**:
```bash
docker stats
```

**Optimize**:
```bash
# Increase memory limit
docker-compose down
# Edit docker-compose.yml, add:
#   deploy:
#     resources:
#       limits:
#         memory: 2G
docker-compose up -d
```

### Container Logs

```bash
# View all logs
./scripts/docker/logs.sh all

# View API logs only
./scripts/docker/logs.sh api

# View last 100 lines
docker-compose logs --tail=100 api

# Follow logs in real-time
docker-compose logs -f api
```

### Restart Services

```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart api

# Rebuild and restart
docker-compose up -d --build api
```

### Clean Start

```bash
# Stop and remove containers
docker-compose down

# Remove volumes (WARNING: deletes data)
docker-compose down -v

# Remove images
docker rmi $(docker images 'rpg_*' -q)

# Fresh start
./scripts/docker/start-dev.sh
```

## Security

### Container Security

**Features**:
- Non-root user (UID 1000)
- Minimal base image (Alpine Linux)
- Read-only file system (where possible)
- Security headers middleware
- Rate limiting

### Network Security

**Isolation**:
- Services run in isolated Docker network
- Only API port (8000) exposed to host
- Database and Redis not accessible from outside

**Firewall Rules** (production):
```bash
# Allow only necessary ports
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw allow 22/tcp   # SSH
sudo ufw enable
```

### Secrets Management

**DO NOT**:
- Commit `.env` to version control
- Use default passwords
- Expose database ports publicly

**DO**:
- Use strong passwords (32+ characters)
- Rotate secrets regularly
- Use Docker secrets for sensitive data
- Enable audit logging

### SSL/TLS Configuration

Use a reverse proxy (Nginx/Caddy) for SSL:

**Example Nginx Config**:
```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Security Scanning

**Scan Images**:
```bash
# Install Trivy
brew install trivy

# Scan image
docker-compose build api
trivy image rpg_api:latest
```

### Monitoring

**Set up monitoring**:
```bash
# Enable metrics
ENABLE_METRICS=true

# Monitor with docker stats
docker stats

# Set up Prometheus + Grafana (optional)
```

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Reference](https://docs.docker.com/compose/compose-file/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [PostgreSQL Docker](https://hub.docker.com/_/postgres)
- [Redis Docker](https://hub.docker.com/_/redis)

## Next Steps

- [Player's Guide](./PLAYER_GUIDE.md) - How to play the game
- [DM's Guide](./DM_GUIDE.md) - How to run game sessions
- [Commands Reference](./COMMANDS.md) - All CLI commands
- [API Documentation](http://localhost:8000/docs) - REST API reference
