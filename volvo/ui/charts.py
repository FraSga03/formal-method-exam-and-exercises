"""Plotly figures for the dashboard. Every builder tolerates an empty result."""
import plotly.express as px
import plotly.graph_objects as go

from volvo.analysis.predictor import MarkovModel
from volvo.logs.loader import ACTIVITY, EventLogBundle
from volvo.mining.performance import case_durations, waiting_times

EMPTY = "No data for this view"


def _empty(title: str) -> go.Figure:
    figure = go.Figure()
    figure.update_layout(title=title, annotations=[{"text": EMPTY, "showarrow": False}])
    return figure


def activity_frequency(bundle: EventLogBundle) -> go.Figure:
    counts = bundle.df[ACTIVITY].value_counts().sort_values()
    return px.bar(
        x=counts.values, y=counts.index, orientation="h",
        labels={"x": "Events", "y": "Activity"}, title="Activity frequency",
    )


def waiting_time_bar(bundle: EventLogBundle, top: int = 10) -> go.Figure:
    table = waiting_times(bundle)
    if table.empty:
        return _empty("Waiting time after each activity")
    table = table.head(top).sort_values("mean_hours")
    figure = go.Figure()
    figure.add_bar(x=table["median_hours"], y=table.index, orientation="h", name="median")
    figure.add_bar(x=table["mean_hours"], y=table.index, orientation="h", name="mean")
    figure.update_layout(
        title="Waiting time after each activity (hours)",
        xaxis_title="Hours", barmode="group",
    )
    return figure


def duration_histogram(bundle: EventLogBundle) -> go.Figure:
    durations = case_durations(bundle)
    return px.histogram(
        x=durations.values, nbins=50,
        labels={"x": "Case duration (hours)"}, title="Case duration distribution",
    )


def transition_heatmap(bundle: EventLogBundle) -> go.Figure:
    matrix = MarkovModel.fit(bundle).transition_matrix()
    if matrix.empty or matrix.to_numpy().sum() == 0:
        return _empty("Transition probabilities")
    return px.imshow(
        matrix, labels={"x": "Next", "y": "Current", "color": "P"},
        title="Transition probabilities", aspect="auto",
    )
