# -*- coding: utf-8 -*-
from django.utils import timezone
from django.utils.translation import gettext as _

import plotly.offline as plotly
import plotly.graph_objs as go

from reports import utils


# Movement threshold to determine sleep
MOVEMENT_SLEEP_THRESHOLD = 30


def owlet_sleep_totals(readings):
    """
    Create a graph showing total sleep time per day based on Owlet movement data.
    :param readings: a QuerySet of OwletReading instances.
    :returns: a tuple of the graph's html and javascript.
    """
    # Filter readings with movement data and order by time
    readings = readings.filter(movement_value__isnull=False).order_by("recorded_at")
    
    if not readings.exists():
        return "", ""
    
    # Calculate sleep totals per day
    daily_sleep = {}
    previous_reading = None
    
    for reading in readings:
        recorded_time = timezone.localtime(reading.recorded_at)
        date_key = recorded_time.date()
        
        # Initialize day if not exists
        if date_key not in daily_sleep:
            daily_sleep[date_key] = 0.0  # hours
        
        # If baby is asleep and we have a previous reading, calculate sleep duration
        if reading.movement_value < MOVEMENT_SLEEP_THRESHOLD and previous_reading:
            prev_time = timezone.localtime(previous_reading.recorded_at)
            
            # Only count if previous reading was also sleep and within reasonable time (< 1 hour)
            time_diff = (recorded_time - prev_time).total_seconds()
            if time_diff < 3600 and previous_reading.movement_value < MOVEMENT_SLEEP_THRESHOLD:
                # Add sleep hours to the day
                sleep_hours = time_diff / 3600
                daily_sleep[date_key] += sleep_hours
        
        previous_reading = reading
    
    # Sort by date
    sorted_dates = sorted(daily_sleep.keys())
    sleep_hours = [daily_sleep[date] for date in sorted_dates]
    
    # Create hover text
    hover_texts = []
    for date, hours in zip(sorted_dates, sleep_hours):
        h = int(hours)
        m = int((hours - h) * 60)
        hover_texts.append(f"{h}h{m}m")
    
    trace = go.Bar(
        name=_("Total sleep"),
        x=sorted_dates,
        y=sleep_hours,
        hoverinfo="text",
        textposition="outside",
        text=hover_texts,
        marker={"color": "rgb(35, 110, 150)"},
    )
    
    layout_args = utils.default_graph_layout_options()
    layout_args["barmode"] = "stack"
    layout_args["title"] = "<b>" + _("Owlet Sleep Totals") + "</b>"
    layout_args["xaxis"]["title"] = _("Date")
    layout_args["xaxis"]["type"] = "date"
    layout_args["xaxis"]["autorange"] = True
    layout_args["xaxis"]["autorangeoptions"] = utils.autorangeoptions(trace.x)
    layout_args["xaxis"]["rangeselector"] = utils.rangeselector_date()
    layout_args["yaxis"]["title"] = _("Hours of sleep")
    layout_args["height"] = 600
    
    fig = go.Figure({"data": [trace], "layout": go.Layout(**layout_args)})
    output = plotly.plot(fig, output_type="div", include_plotlyjs=False)
    return utils.split_graph_output(output)
