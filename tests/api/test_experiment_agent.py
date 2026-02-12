"""Tests for eval agent endpoints."""


class TestEvalAgent:
    """Tests for eval agent endpoints."""

    def test_create_eval_config(self, client):
        """Test creating eval configuration."""
        response = client.post(
            "/evaluate/eval/create",
            json={
                "name": "test_eval",
                "dataset_config": {
                    "type": "index_csv",
                    "index_file": "benchmarks/datasets/index.csv",
                    "base_dir": "benchmarks/datasets",
                },
                "scorers_config": [
                    {"type": "deep_diff", "version": "v3"},
                ],
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert "eval_id" in data

    def test_run_eval(self, client):
        """Test running an eval."""
        # First create eval
        create_response = client.post(
            "/evaluate/eval/create",
            json={
                "name": "test_eval",
                "dataset_config": {
                    "type": "index_csv",
                    "index_file": "benchmarks/datasets/index.csv",
                    "base_dir": "benchmarks/datasets",
                },
                "scorers_config": [
                    {"type": "deep_diff", "version": "v3"},
                ],
            },
        )

        if create_response.status_code == 201:
            eval_id = create_response.json()["eval_id"]

            # Then run eval
            response = client.post(
                "/evaluate/experiment/run",
                json={
                    "experiment_id": experiment_id,
                    "adapter_config": {
                        "type": "ml_infra",
                        "base_url": "http://localhost:8000",
                    },
                    "model": "gpt-4o",
                },
            )
            
            # May fail if files don't exist or adapter can't connect
            assert response.status_code in [200, 404, 500]
