import logging

import click
from click_help_colors import HelpColorsGroup, HelpColorsCommand

from .collect import update_metrics_file, MetricsWriter, get_github_client

logging.basicConfig(format="%(message)s", level=logging.INFO)


@click.group(
    cls=HelpColorsGroup, help_headers_color="yellow", help_options_color="green"
)
@click.pass_context
def main(ctx):
    """Entry point for the oss-metrics CLI."""


@main.command(cls=HelpColorsCommand)
@click.argument("repositories", nargs=-1)
@click.option(
    "--backlog-weeks",
    default=1,
    help="Backlog weeks; when running for the first time, set to 52.",
)
@click.option("--file", help="File to save metrics to.", default="metrics.json")
@click.pass_context
def collect(repositories, backlog_weeks, file):
    """
    Collect metrics for one or more GitHub repositories.

    TODO: Write a validator for `repositories` to ensure they are valid GitHub repository names (e.g. `owner/repo`).
    """
    gh = get_github_client()
    metrics_writer = MetricsWriter(file)

    update_metrics_file(gh, metrics_writer, repositories, backlog_weeks)


@main.command(cls=HelpColorsCommand)
@click.argument("repositories", nargs=-1)
def build(repositories):
    """Build metrics for one or more GitHub repositories."""
    pass
