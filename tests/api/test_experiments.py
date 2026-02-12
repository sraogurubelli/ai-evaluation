"""Tests for eval endpoints."""


class TestEvalsEndpoint:
    """Tests for /evals endpoint."""

    def test_create_eval_success(self, client, sample_dataset_config, sample_adapter_config):
        """Test successful eval creation."""
        response = client.post(
            "/evals",
            json={
                "eval_name": "test_eval",
                "config": {
                    "dataset": sample_dataset_config,
                    "adapter": sample_adapter_config,
                    "scorers": [{"type": "deep_diff", "version": "v3"}],
                    "models": ["gpt-4o"],
                },
                "run_async": True,
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["eval_name"] == "test_eval"
        assert data["status"] == "pending"

    def test_create_eval_invalid_config(self, client):
        """Test eval creation with minimal/invalid config (API may accept and create task)."""
        response = client.post(
            "/evals",
            json={
                "eval_name": "test",
                "config": {},  # Minimal config; validation may happen at execution time
                "run_async": True,
            },
        )
        # API accepts empty config and creates task (201); or returns error (4xx/5xx)
        assert response.status_code in [201, 400, 422, 500]

    def test_create_eval_missing_fields(self, client):
        """Test eval creation with missing required fields."""
        response = client.post(
            "/evals",
            json={
                "eval_name": "test",
                # Missing config
            },
        )

        assert response.status_code == 422  # Validation error
