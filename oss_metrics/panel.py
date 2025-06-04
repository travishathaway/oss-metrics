"""
Contains Panel components for displaying metrics in a web application.
"""

from __future__ import annotations

from collections.abc import Sequence

import panel as pn
import pandas as pd

from .types import RowTypes


ROW_TYPE_NAME_MAPPING = {
    "new_issues": "New Issues",
    "open_issues": "Open Issues",
    "open_pull_requests": "Open Pull Requests",
    "closed_pull_requests": "Closed Pull Requests",
}


def create_dashboard(
    metrics_data: dict[RowTypes, dict[str, str | int]], output: str = None
):
    """
    Create a Panel dashboard with a shared dropdown to select a project and update all charts accordingly.
    """

    # Convert metrics data to DataFrame
    def get_projects(data: dict[RowTypes, dict[str, str | int]]) -> Sequence[str]:
        projects = set()
        for chart_data in data.values():
            for entry in chart_data:
                project = f"{entry['org']}/{entry['repository']}"
                projects.add(project)
        return sorted(projects)

    project_select = pn.widgets.Select(
        name="Project", options=get_projects(metrics_data)
    )

    def get_line_chart(data, chart: RowTypes):
        title = ROW_TYPE_NAME_MAPPING.get(chart, chart)
        df = pd.DataFrame(data[chart])
        df["date"] = pd.to_datetime(df["date"])
        df["project"] = df["org"] + "/" + df["repository"]

        @pn.depends(project=project_select)
        def line_chart(project):
            filtered = df[df["project"] == project]
            grouped = filtered.groupby("date")["count"].sum().reset_index()
            return grouped.hvplot.line(
                x="date",
                y="count",
                value_labels={"count": "Count", "date": "Date"},
                title=title,
                width=800,
                height=400,
                shared_axes=False,
            )

        return line_chart

    charts = [get_line_chart(metrics_data, chart) for chart in metrics_data.keys()]

    dashboard = pn.Column(
        pn.pane.Markdown("# GitHub Metrics Dashboard"),
        project_select,
        *charts,
    )

    if output:
        dashboard.save(output, embed=True)
    return dashboard
