import pytest
from click.testing import CliRunner
from oss_metrics.cli import main


@pytest.fixture
def runner():
    return CliRunner()


def test_build(runner):
    result = runner.invoke(main, ["build", "repo1", "repo2"])
    assert result.exit_code == 0
