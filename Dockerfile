# Multi-stage Dockerfile for LLM Dungeon Master
# Optimized for production deployment with security hardening


# Stage 1: Base image with UV package manager
FROM python:3.12-slim as base

# Install system dependencies and UV
RUN apt-get update && apt-get install -y \
    curl \
    && curl -LsSf https://astral.sh/uv/install.sh | sh \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Add UV to PATH
ENV PATH="/root/.cargo/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml README.md ./

# Stage 2: Development environment (with hot reload)
FROM base as development

# Install dependencies with UV (development mode)
RUN uv pip install --system -e .

# Copy source code
COPY src/ ./src/
COPY test/ ./test/

# Create non-root user for security
RUN useradd -m -u 1000 rpguser && \
    chown -R rpguser:rpguser /app

USER rpguser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Default command for development (hot reload)
CMD ["python", "-m", "uvicorn", "llm_dungeon_master.server:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Stage 3: Production environment (optimized)
FROM base as production

# Install dependencies with UV (production mode, no dev dependencies)
RUN uv pip install --system .

# Copy only source code (not tests)
COPY src/ ./src/

# Create non-root user for security
RUN useradd -m -u 1000 rpguser && \
    chown -R rpguser:rpguser /app && \
    mkdir -p /app/logs /app/data && \
    chown -R rpguser:rpguser /app/logs /app/data

USER rpguser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Default command for production (optimized)
CMD ["python", "-m", "uvicorn", "llm_dungeon_master.server:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
