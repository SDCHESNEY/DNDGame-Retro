"""Tests for enhanced server endpoints (health checks, monitoring)."""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine, Session as DBSession
from sqlmodel.pool import StaticPool

from llm_dungeon_master.server import app, get_db


# Create test database
@pytest.fixture(name="session")
def session_fixture():
    """Create test database session."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with DBSession(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: DBSession):
    """Create test client with database override."""
    def get_session_override():
        return session
    
    app.dependency_overrides[get_db] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


class TestHealthEndpoints:
    """Test health check endpoints."""
    
    def test_health_endpoint_basic(self, client):
        """Test basic health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "version" in data
        assert "checks" in data
    
    def test_health_endpoint_includes_database_check(self, client):
        """Test health check includes database connectivity."""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "checks" in data
        assert "database" in data["checks"]
        assert data["checks"]["database"] == "healthy"
    
    def test_health_endpoint_includes_llm_provider(self, client):
        """Test health check includes LLM provider status."""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "checks" in data
        assert "llm_provider" in data["checks"]
        assert "llm_model" in data["checks"]
    
    def test_health_endpoint_status_healthy(self, client):
        """Test health check returns healthy status."""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        # With a working database, should be healthy
        assert data["status"] in ["healthy", "degraded"]
    
    def test_ready_endpoint(self, client):
        """Test readiness check endpoint."""
        response = client.get("/ready")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert data["status"] == "ready"
        assert "timestamp" in data
    
    def test_live_endpoint(self, client):
        """Test liveness check endpoint."""
        response = client.get("/live")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert data["status"] == "alive"
        assert "timestamp" in data


class TestRootEndpoint:
    """Test root endpoint."""
    
    def test_root_endpoint(self, client):
        """Test root endpoint returns welcome message."""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "docs" in data
        assert data["docs"] == "/docs"


class TestHealthIntegration:
    """Integration tests for health check system."""
    
    def test_all_health_endpoints_accessible(self, client):
        """Test all health check endpoints are accessible."""
        endpoints = ["/health", "/ready", "/live"]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 200, f"Endpoint {endpoint} failed"
    
    def test_health_endpoints_return_timestamps(self, client):
        """Test all health endpoints include timestamps."""
        endpoints = ["/health", "/ready", "/live"]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            data = response.json()
            assert "timestamp" in data, f"Endpoint {endpoint} missing timestamp"
    
    def test_health_check_versioning(self, client):
        """Test health check includes version information."""
        response = client.get("/health")
        data = response.json()
        
        assert "version" in data
        assert data["version"] == "0.1.0"
