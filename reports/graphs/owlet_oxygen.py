# -*- coding: utf-8 -*-
from django.utils import timezone
from django.utils.translation import gettext as _

import plotly.offline as plotly
import plotly.graph_objs as go

from reports import utils


def owlet_oxygen(readings):
    """
    Create a graph showing oxygen saturation readings over time from Owlet device.
    :param readings: a QuerySet of OwletReading instances.
    :returns: a tuple of the graph's html and javascript.
    """
    # Filter out readings without oxygen data
    readings = readings.filter(oxygen_saturation_pct__isnull=False).order_by("recorded_at")
    
    if not readings.exists():
        return "", ""
    
    # Prepare data
    times = []
    oxygen_levels = []
    hover_texts = []
    
    for reading in readings:
        recorded_time = timezone.localtime(reading.recorded_at)
        times.append(recorded_time)
        oxygen_levels.append(reading.oxygen_saturation_pct)
        hover_texts.append(
            f"{int(reading.oxygen_saturation_pct)}%<br>{recorded_time.strftime('%Y-%m-%d %H:%M:%S')}"
        )
    
    # Create trace
    trace = go.Scatter(
        x=times,
        y=oxygen_levels,
        mode="lines+markers",
        name=_("Oxygen Saturation"),
        line={"color": "rgb(54, 162, 235)"},
        marker={"size": 4},
        hovertext=hover_texts,
        hoverinfo="text",
    )
    
    # Add normal range reference lines
    normal_low = go.Scatter(
        x=[times[0], times[-1]],
        y=[95, 95],
        mode="lines",
        name=_("Normal Range Low (95%)"),
        line={"color": "rgba(75, 192, 192, 0.5)", "dash": "dash"},
        hoverinfo="skip",
    )
    
    alert_threshold = go.Scatter(
        x=[times[0], times[-1]],
        y=[80, 80],
        mode="lines",
        name=_("Alert Threshold (80%)"),
        line={"color": "rgba(255, 99, 132, 0.5)", "dash": "dash"},
        hoverinfo="skip",
    )
    
    layout_args = utils.default_graph_layout_options()
    layout_args["title"] = "<b>" + _("Owlet Oxygen Saturation") + "</b>"
    layout_args["xaxis"]["title"] = _("Date and Time")
    layout_args["xaxis"]["type"] = "date"
    layout_args["xaxis"]["rangeselector"] = utils.rangeselector_time()
    layout_args["yaxis"]["title"] = _("Oxygen Saturation (%)")
    layout_args["yaxis"]["range"] = [75, 100]
    layout_args["height"] = 600
    
    fig = go.Figure(
        {"data": [trace, normal_low, alert_threshold], "layout": go.Layout(**layout_args)}
    )
    output = plotly.plot(fig, output_type="div", include_plotlyjs=False)
    return utils.split_graph_output(output)
