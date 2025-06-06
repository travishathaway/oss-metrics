import json
import logging
import sys

import click
from click_help_colors import HelpColorsGroup, HelpColorsCommand

from .collect import update_metrics_file, MetricsWriter, get_github_client
from .panel import create_dashboard


@click.group(
    cls=HelpColorsGroup, help_headers_color="yellow", help_options_color="green"
)
@click.option(
    "-v",
    "--verbose",
    count=True,
    help="Increase verbosity. Use -v for info, -vv for debug.",
)
@click.pass_context
def main(ctx, verbose):
    """Entry point for the oss-metrics CLI."""
    # Map verbosity to logging levels
    if verbose == 2:
        level = logging.DEBUG
    elif verbose == 1:
        level = logging.INFO
    else:
        level = logging.WARNING

    logging.basicConfig(format="%(message)s", level=level)
    logging.getLogger().setLevel(level)
    ctx.ensure_object(dict)
    ctx.obj["VERBOSE"] = verbose


@main.command(cls=HelpColorsCommand)
@click.argument("repositories", nargs=-1)
@click.option(
    "--backlog-weeks",
    default=1,
    help="Backlog weeks; defaults to 1; when running for the first time, set to 52.",
)
@click.option("--output", "-o", help="File to save metrics to.", default="metrics.json")
@click.pass_context
def collect(ctx, repositories, backlog_weeks, output):
    """
    Collect metrics for one or more GitHub repositories.

    TODO: Write a validator for `repositories` to ensure they are valid GitHub repository names (e.g. `owner/repo`).
    """
    gh = get_github_client()
    metrics_writer = MetricsWriter(output)

    update_metrics_file(gh, metrics_writer, repositories, backlog_weeks)


@main.command(cls=HelpColorsCommand)
@click.argument("metrics_file", type=click.Path(exists=True))
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    default="dashboard.html",
    help="Output HTML file.",
)
def build(metrics_file, output):
    """
    Builds a metrics dashboard and renders it as a HTML file.
    """
    try:
        with open(metrics_file, "r") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        click.echo(f"Error reading metrics file: {e}", err=True)
        sys.exit(1)

    if data:
        create_dashboard(data, output=output)
