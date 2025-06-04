from __future__ import annotations

from datetime import datetime
from dataclasses import dataclass
from typing import Literal


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
