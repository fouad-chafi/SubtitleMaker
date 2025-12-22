"""Tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient

from src.api.main import create_app
from src.models.config import Settings


@pytest.fixture
def client():
    """Create a test client."""
    app = create_app(Settings())
    return TestClient(app)


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    def test_health_check(self, client):
        """Test basic health check."""
        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "version" in data
        assert "gpu_available" in data

    def test_gpu_info(self, client):
        """Test GPU info endpoint."""
        response = client.get("/api/v1/health/gpu")

        assert response.status_code == 200
        data = response.json()
        assert "available" in data
        assert "vram_total_mb" in data
