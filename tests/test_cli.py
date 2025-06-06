import os
import json
from pathlib import Path

import pytest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

from oss_metrics.cli import main


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def report_html_path(tmp_path) -> Path:
    """
    Returns a path to a temporary HTML file for the report.
    """
    report_html = tmp_path / "dashboard.html"

    return report_html


@pytest.fixture
def metrics_path() -> Path:
    """
    Returns the path to the metrics JSON file.
    """
    return Path(os.path.join(os.path.dirname(__file__), "data", "metrics.json"))


@pytest.fixture(autouse=True)
def mock_github_api():
    """
    Automatically mock all calls to the GitHub API for tests in this module.
    """
    mock_github = MagicMock()
    mock_repo = MagicMock()
    mock_github.get_repo.return_value = mock_repo

    # Simulate real issue and pull request objects
    mock_issue = MagicMock()
    mock_issue.title = "Test Issue"
    mock_issue.number = 1
    mock_issue.state = "open"
    mock_issue.created_at = "2024-01-01T00:00:00Z"
    mock_issue.closed_at = None

    mock_pr = MagicMock()
    mock_pr.title = "Test PR"
    mock_pr.number = 2
    mock_pr.state = "closed"
    mock_pr.created_at = "2024-01-02T00:00:00Z"
    mock_pr.closed_at = "2024-01-03T00:00:00Z"

    mock_repo.get_issues.return_value = [mock_issue]
    mock_repo.get_pulls.return_value = [mock_pr]
    mock_github.search_issues.return_value.totalCount = 1

    with patch("oss_metrics.collect.Github", return_value=mock_github):
        yield


def test_build(runner, report_html_path, metrics_path):
    """
    Run build command with data in data/metrics.json
    """
    result = runner.invoke(
        main, ["build", str(metrics_path), "--output", str(report_html_path)]
    )

    assert result.exit_code == 0
    assert report_html_path.exists()


def test_assert_no_warnings_for_build_command(
    runner, report_html_path, metrics_path, caplog
):
    result = runner.invoke(
        main, ["-v", "build", str(metrics_path), "--output", str(report_html_path)]
    )
    assert result.exit_code == 0
    assert "WARNING" not in caplog.text


def test_collect(runner, tmp_path, mock_github_api, mocker):
    """
    Run the collect command with a mocked GitHub API
    """
    metrics_path = tmp_path / "metrics.json"
    mocker.patch("oss_metrics.collect.GITHUB_TOKEN", "abc123")
    result = runner.invoke(
        main,
        [
            "collect",
            "owner/repo",
            "--backlog-weeks",
            "1",
            "--output",
            str(metrics_path),
        ],
    )

    data = json.loads(metrics_path.read_text())
    expected_keys = {
        "open_issues",
        "open_pull_requests",
        "closed_issues",
        "closed_pull_requests",
        "new_issues",
    }

    assert result.exit_code == 0
    assert set(data.keys()).difference(expected_keys) == set()

    assert data["open_issues"][0]["repository"] == "repo"
    assert data["open_issues"][0]["org"] == "owner"
    assert data["open_issues"][0]["count"] == 2
    assert (
        data["open_issues"][0]["date"] is not None
    )  # TODO: add actually check for date
