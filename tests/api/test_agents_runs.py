"""Integration tests for agents and runs API endpoints.

Covers GET /agents, GET /agents/{agent_id}/runs, GET /runs/{run_id},
GET /runs/{run_id}/report, and POST /agents/{agent_id}/runs.
Uses the in-memory _pushed_runs store; each test gets a clean state via
the clear_pushed_runs fixture. Run in single-process mode (do not use
pytest-xdist -n auto) because tests mutate the shared _pushed_runs list.
"""

import uuid

import pytest
import aieval.api.app as app_module
from tests.api.conftest import client


@pytest.fixture(autouse=True)
def clear_pushed_runs():
    """Clear in-memory pushed runs before and after each test for isolation."""
    app_module._pushed_runs.clear()
    try:
        yield
    finally:
        app_module._pushed_runs.clear()


def _sample_push_payload(run_id: str = "run-integration-1", agent_name: str | None = "Test Agent"):
    """Minimal valid body for POST /agents/{agent_id}/runs."""
    return {
        "run_id": run_id,
        "experiment_id": "exp-1",
        "dataset_id": "ds-1",
        "scores": [
            {
                "name": "pass",
                "value": 1.0,
                "eval_id": "test.v1",
                "metadata": {"test_id": "test-001"},
            },
        ],
        "metadata": {"model": "test-model", "agent_name": agent_name},
    }


@pytest.mark.api
@pytest.mark.integration
class TestAgentsRunsEndpoints:
    """Integration tests for agent and run consolidation endpoints."""

    def test_list_agents_empty(self, client):
        """GET /agents with no pushed runs returns empty or task-derived agents."""
        response = client.get("/agents")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_push_run_then_list_agents(self, client):
        """POST a run then GET /agents includes the agent."""
        agent_id = "agent-integration-1"
        payload = _sample_push_payload()
        r = client.post(f"/agents/{agent_id}/runs", json=payload)
        assert r.status_code == 201
        body = r.json()
        assert body.get("run_id") == payload["run_id"]
        assert body.get("agent_id") == agent_id

        agents = client.get("/agents").json()
        ids = [a["agent_id"] for a in agents]
        assert agent_id in ids
        agent = next(a for a in agents if a["agent_id"] == agent_id)
        assert agent["run_count"] >= 1
        assert agent.get("agent_name") == "Test Agent"

    def test_push_run_then_list_agent_runs(self, client):
        """POST a run then GET /agents/{agent_id}/runs returns the run."""
        agent_id = "agent-integration-2"
        payload = _sample_push_payload(run_id="run-integration-2")
        client.post(f"/agents/{agent_id}/runs", json=payload)
        response = client.get(f"/agents/{agent_id}/runs")
        assert response.status_code == 200
        runs = response.json()
        assert len(runs) >= 1
        run_ids = [r["run_id"] for r in runs]
        assert "run-integration-2" in run_ids

    def test_get_run_by_id(self, client):
        """POST a run then GET /runs/{run_id} returns full run detail (pushed path)."""
        agent_id = "agent-integration-3"
        run_id = f"run-{uuid.uuid4().hex}"  # unique so we hit pushed-run path only
        payload = _sample_push_payload(run_id=run_id)
        client.post(f"/agents/{agent_id}/runs", json=payload)

        response = client.get(f"/runs/{run_id}")
        assert response.status_code == 200
        run = response.json()
        assert run["run_id"] == run_id
        assert run["experiment_id"] == payload["experiment_id"]
        assert len(run["scores"]) == len(payload["scores"])
        assert run["metadata"].get("agent_id") == agent_id
        # Response should include dataset_id (pushed run payload has it)
        if "dataset_id" in run:
            assert run["dataset_id"] == payload["dataset_id"]

    def test_get_run_not_found(self, client):
        """GET /runs/{run_id} for non-existent run returns 404."""
        response = client.get("/runs/nonexistent-run-id")
        assert response.status_code == 404

    def test_get_run_report(self, client):
        """POST a run then GET /runs/{run_id}/report returns HTML."""
        agent_id = "agent-integration-4"
        run_id = "run-integration-4"
        payload = _sample_push_payload(run_id=run_id)
        client.post(f"/agents/{agent_id}/runs", json=payload)

        response = client.get(f"/runs/{run_id}/report")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")
        html_content = response.text
        assert run_id in html_content or "Run" in html_content

    def test_get_run_report_not_found(self, client):
        """GET /runs/{run_id}/report for non-existent run returns 404."""
        response = client.get("/runs/nonexistent-run-id/report")
        assert response.status_code == 404

    def test_list_agent_runs_pagination(self, client):
        """List agent runs with limit and offset."""
        agent_id = "agent-integration-pag"
        client.post(
            f"/agents/{agent_id}/runs",
            json=_sample_push_payload(run_id="run-pag-1"),
        )
        client.post(
            f"/agents/{agent_id}/runs",
            json=_sample_push_payload(run_id="run-pag-2"),
        )

        full = client.get(f"/agents/{agent_id}/runs").json()
        assert len(full) >= 2

        page1 = client.get(f"/agents/{agent_id}/runs?limit=1&offset=0").json()
        assert len(page1) == 1
        page2 = client.get(f"/agents/{agent_id}/runs?limit=1&offset=1").json()
        assert len(page2) == 1
        assert page1[0]["run_id"] != page2[0]["run_id"]

    def test_push_run_metadata_agent_name(self, client):
        """Pushed run metadata can include agent_name; list_agents shows it."""
        agent_id = "agent-name-test"
        payload = _sample_push_payload(run_id="run-name-1", agent_name="My CI Agent")
        client.post(f"/agents/{agent_id}/runs", json=payload)

        agents = client.get("/agents").json()
        agent = next((a for a in agents if a["agent_id"] == agent_id), None)
        assert agent is not None
        assert agent.get("agent_name") == "My CI Agent"

    def test_push_run_invalid_payload_returns_422(self, client):
        """POST /agents/{agent_id}/runs with invalid body returns 422."""
        agent_id = "agent-422"
        # Missing required fields: run_id, experiment_id, dataset_id, scores
        invalid_payload = {"metadata": {}}
        response = client.post(f"/agents/{agent_id}/runs", json=invalid_payload)
        assert response.status_code == 422

    def test_list_agent_runs_unknown_agent_returns_empty(self, client):
        """GET /agents/{agent_id}/runs for agent with no runs returns empty list."""
        agent_id = "agent-nonexistent-" + uuid.uuid4().hex[:8]
        response = client.get(f"/agents/{agent_id}/runs")
        assert response.status_code == 200
        assert response.json() == []
