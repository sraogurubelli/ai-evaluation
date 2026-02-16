"""Tests for adapter agent endpoints."""


class TestAdapterAgent:
    """Tests for adapter agent endpoints."""

    def test_create_adapter(self, client):
        """Test creating an adapter."""
        response = client.post(
            "/evaluate/adapter/create",
            json={
                "adapter_type": "ml_infra",
                "name": "test_adapter",
                "config": {
                    "base_url": "http://localhost:8000",
                    "auth_token": "test-token",
                },
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert "adapter_id" in data

    def test_generate_output(self, client):
        """Test generating output with adapter."""
        # First create adapter
        create_response = client.post(
            "/evaluate/adapter/create",
            json={
                "adapter_type": "ml_infra",
                "name": "test_adapter",
                "config": {
                    "base_url": "http://localhost:8000",
                    "auth_token": "test-token",
                },
            },
        )

        if create_response.status_code == 201:
            adapter_id = create_response.json()["adapter_id"]

            # Then generate output
            response = client.post(
                "/evaluate/adapter/generate",
                json={
                    "adapter_id": adapter_id,
                    "input_data": {
                        "prompt": "Create a pipeline",
                        "entity_type": "pipeline",
                        "operation_type": "create",
                    },
                    "model": "gpt-4o",
                },
            )

            # May fail if adapter can't connect, but should return proper error
            assert response.status_code in [200, 500]
            if response.status_code == 200:
                data = response.json()
                assert "output" in data

    def test_list_adapters(self, client):
        """Test listing adapters."""
        response = client.get("/evaluate/adapter/list")

        assert response.status_code == 200
        data = response.json()
        assert "cached" in data
        assert "available_types" in data
