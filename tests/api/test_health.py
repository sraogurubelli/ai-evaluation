"""Tests for health check endpoint."""


def test_health_check(client):
    """Test health check endpoint (GET /health)."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    # Router health returns timestamp/checks; legacy returns tasks
    assert "timestamp" in data or "tasks" in data
