"""
Contains the logic for fetching and processing GitHub metrics.
"""

from __future__ import annotations

import os
import json
import logging
import time
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from string import Template
from typing import Literal

from github import Github, GithubException

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class MetricsRow:
    """
    Represents a row of metrics data.
    """

    repository: str
    org: str
    count: int
    date: datetime

    def to_json(self) -> dict[str, str | int]:
        """
        Converts the row to a JSON serializable dictionary.

        :return: dict
        """
        return {
            "repository": self.repository,
            "org": self.org,
            "count": self.count,
            "date": self.date.isoformat(),
        }


RowTypes = Literal[
    "new_issues", "open_issues", "open_pull_requests", "closed_pull_requests"
]

QUERY_TEMPLATES: dict[Literal, tuple[Template, ...]] = {
    "new_issues": (Template("repo:$org/$repo_name is:issue created:$start..$end"),),
    "open_issues": (
        # Currently open, but created before the end of the search window
        Template("repo:$org/$repo_name is:issue is:open created:<$end"),
        # Currently closed, but created before the end of the search window,
        # and closed after the end of the search window.
        Template("repo:$org/$repo_name is:issue created:<$end closed:>=$end"),
    ),
    "open_pull_requests": (
        # Currently open, but created before the end of the search window
        Template("repo:$org/$repo_name is:pr is:open created:<$end"),
        # Currently closed, but created before the end of the search window,
        # and closed after the end of the search window.
        Template("repo:$org/$repo_name is:pr created:<$end closed:>=$end"),
    ),
    "closed_pull_requests": (
        Template("repo:$org/$repo_name is:pr closed:$start..$end"),
    ),
}


class MetricsWriter:
    """
    Writes metrics as a JSON file.
    """

    def __init__(self, output_file: str):
        self.output_file = output_file
        self.data = self._load_data(output_file)

    def add_row(self, row_type: RowTypes, row: MetricsRow) -> None:
        """
        Adds a new row to the metrics file.

        :param row:
        :return:
        """
        if not isinstance(row, MetricsRow):
            raise TypeError("row must be an instance of MetricsRow")

        if row_type not in self.data:
            raise ValueError(
                f"Invalid row type: {row_type}. Must be one of {list(self.data.keys())}."
            )

        self.data[row_type].append(row.to_json())
        logger.debug(f"Added row: {row}")

    @staticmethod
    def _load_data(output_file: str) -> dict[RowTypes, list[dict[str, str | int]]]:
        """
        Opens the file and loads the data.

        :return: file object
        """
        try:
            with open(output_file, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.debug("File not found, initializing with empty data.")
            return {
                "new_issues": [],
                "open_issues": [],
                "open_pull_requests": [],
                "closed_pull_requests": [],
            }

    def save(self) -> None:
        """
        Saves the current data to the output file.
        """
        with open(self.output_file, "w") as f:
            json.dump(self.data, f, indent=4, default=str)
        logger.debug(f"Metrics saved to {self.output_file}")


def get_github_client():
    """
    Returns a GitHub client authenticated with the GITHUB_TOKEN environment variable.
    If the token is not set, it raises an error.
    """
    if not GITHUB_TOKEN:
        raise ValueError("GITHUB_TOKEN environment variable is not set.")

    return Github(GITHUB_TOKEN)


def robust_gh_count(gh: Github, query: str):
    """
    Counts the number of issues or pull requests matching a query.

    Contains logic for retrying on rate limits.

    :param gh:
    :param query:
    :return:
    """
    count = None
    while count is None:
        try:
            logger.info(f"{query=}")
            results = gh.search_issues(query=query)
            count = results.totalCount
        except GithubException as e:
            if e.status == 403:
                reset = gh.get_rate_limit().search.reset
                print(
                    f"rate limited until {reset} (currently {datetime.now(timezone.utc)})..."
                )
                while gh.get_rate_limit().search.remaining == 0:
                    time.sleep(1)
            else:
                print(e)

    return count


def update_metrics_file(
    gh: Github,
    metrics_writer: MetricsWriter,
    repositories: Sequence[str],
    backlog_weeks: int = 1,
) -> None:
    """
    Updates the metrics file with the current data.

    :param gh: GitHub client instance
    :param metrics_writer: MetricsWriter instance
    :param repositories: repositories to update
    :param backlog_weeks: number of weeks to look back for metrics
    """
    for row in range(backlog_weeks, -1, -1):
        end_date = datetime.now(timezone.utc) - timedelta(weeks=row)
        for row_type, query_templates in QUERY_TEMPLATES.items():
            for repo in repositories:
                logger.info(
                    f"Processing {row_type} for {repo} on {end_date.strftime('%Y-%m-%d')}"
                )

                organization, name = repo.split("/")
                end = end_date.strftime("%Y-%m-%d")
                start = (end_date - timedelta(days=30)).strftime("%Y-%m-%d")

                count = sum(
                    robust_gh_count(
                        gh,
                        template.substitute(
                            org=organization, repo_name=name, start=start, end=end
                        ),
                    )
                    for template in query_templates
                )

                metrics_row = MetricsRow(
                    repository=name, org=organization, count=count, date=end_date
                )
                metrics_writer.add_row(row_type, metrics_row)

    metrics_writer.save()
