import pytest
from click.testing import CliRunner
from oss_metrics.cli import main
import logging


@pytest.fixture
def runner():
    return CliRunner()


def test_build(runner):
    result = runner.invoke(main, ["build", "repo1", "repo2"])
    assert result.exit_code == 0


def test_verbose_flag_sets_info_level(runner, monkeypatch):
    logs = []

    def fake_basicConfig(format, level):
        logs.append(level)

    monkeypatch.setattr(logging, "basicConfig", fake_basicConfig)
    result = runner.invoke(main, ["-v", "build", "repo1"])
    assert result.exit_code == 0
    assert logging.INFO in logs


def test_double_verbose_flag_sets_debug_level(runner, monkeypatch):
    logs = []

    def fake_basicConfig(format, level):
        logs.append(level)

    monkeypatch.setattr(logging, "basicConfig", fake_basicConfig)
    result = runner.invoke(main, ["-vv", "build", "repo1"])
    assert result.exit_code == 0
    assert logging.DEBUG in logs


def test_triple_verbose_flag_sets_trace_level(runner, monkeypatch):
    logs = []

    def fake_basicConfig(format, level):
        logs.append(level)

    monkeypatch.setattr(logging, "basicConfig", fake_basicConfig)
    result = runner.invoke(main, ["-vvv", "build", "repo1"])
    assert result.exit_code == 0
    assert 5 in logs  # TRACE level is set to 5
