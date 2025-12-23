# -*- coding: utf-8 -*-
from django.utils import timezone
from django.utils.translation import gettext as _

import plotly.offline as plotly
import plotly.graph_objs as go

from reports import utils


def owlet_heart_rate(readings):
    """
    Create a graph showing heart rate readings over time from Owlet device.
    :param readings: a QuerySet of OwletReading instances.
    :returns: a tuple of the graph's html and javascript.
    """
    # Filter out readings without heart rate data
    readings = readings.filter(heart_rate_bpm__isnull=False).order_by("recorded_at")
    
    if not readings.exists():
        return "", ""
    
    # Prepare data
    times = []
    heart_rates = []
    hover_texts = []
    
    for reading in readings:
        recorded_time = timezone.localtime(reading.recorded_at)
        times.append(recorded_time)
        heart_rates.append(reading.heart_rate_bpm)
        hover_texts.append(
            f"{int(reading.heart_rate_bpm)} bpm<br>{recorded_time.strftime('%Y-%m-%d %H:%M:%S')}"
        )
    
    # Create trace
    trace = go.Scatter(
        x=times,
        y=heart_rates,
        mode="lines+markers",
        name=_("Heart Rate"),
        line={"color": "rgb(255, 99, 132)"},
        marker={"size": 4},
        hovertext=hover_texts,
        hoverinfo="text",
    )
    
    # Add normal range reference lines
    normal_low = go.Scatter(
        x=[times[0], times[-1]],
        y=[80, 80],
        mode="lines",
        name=_("Normal Range Low (80 bpm)"),
        line={"color": "rgba(255, 255, 255, 0.3)", "dash": "dash"},
        hoverinfo="skip",
    )
    
    normal_high = go.Scatter(
        x=[times[0], times[-1]],
        y=[180, 180],
        mode="lines",
        name=_("Normal Range High (180 bpm)"),
        line={"color": "rgba(255, 255, 255, 0.3)", "dash": "dash"},
        hoverinfo="skip",
    )
    
    layout_args = utils.default_graph_layout_options()
    layout_args["title"] = "<b>" + _("Owlet Heart Rate") + "</b>"
    layout_args["xaxis"]["title"] = _("Date and Time")
    layout_args["xaxis"]["type"] = "date"
    layout_args["xaxis"]["rangeselector"] = utils.rangeselector_time()
    layout_args["yaxis"]["title"] = _("Heart Rate (bpm)")
    layout_args["yaxis"]["range"] = [60, 200]
    layout_args["height"] = 600
    
    fig = go.Figure(
        {"data": [trace, normal_low, normal_high], "layout": go.Layout(**layout_args)}
    )
    output = plotly.plot(fig, output_type="div", include_plotlyjs=False)
    return utils.split_graph_output(output)
