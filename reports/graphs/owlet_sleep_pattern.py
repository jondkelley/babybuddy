# -*- coding: utf-8 -*-
from collections import OrderedDict
from datetime import timedelta

from django.utils import timezone, formats
from django.utils.translation import gettext as _

import plotly.offline as plotly
import plotly.graph_objs as go
import plotly.colors as colors

from reports import utils


# Movement threshold to determine sleep vs wake
# Lower movement values indicate sleep, higher values indicate awake
MOVEMENT_SLEEP_THRESHOLD = 30

ASLEEP_COLOR = "rgb(35, 110, 150)"
AWAKE_COLOR = colors.DEFAULT_PLOTLY_COLORS[2]


def owlet_sleep_pattern(readings):
    """
    Create a graph showing sleep/wake patterns based on Owlet movement data.
    :param readings: a QuerySet of OwletReading instances.
    :returns: a tuple of the graph's html and javascript.
    """
    # Filter readings with movement data and order by time
    readings = readings.filter(movement_value__isnull=False).order_by("recorded_at")
    
    if not readings.exists():
        return "", ""
    
    first_reading = readings.first()
    last_reading = readings.last()
    first_day = timezone.localtime(first_reading.recorded_at)
    last_day = timezone.localtime(last_reading.recorded_at)
    
    days = _init_days(first_day, last_day)
    
    # Process readings into sleep/wake periods
    current_state = None  # 'asleep' or 'awake'
    state_start_time = None
    
    for reading in readings:
        recorded_time = timezone.localtime(reading.recorded_at)
        date_key = recorded_time.date().isoformat()
        
        # Determine if baby is asleep or awake based on movement
        is_asleep = reading.movement_value < MOVEMENT_SLEEP_THRESHOLD
        new_state = 'asleep' if is_asleep else 'awake'
        
        # Initialize state tracking
        if current_state is None:
            current_state = new_state
            state_start_time = recorded_time.replace(hour=0, minute=0, second=0)
        
        # State change detected
        if new_state != current_state:
            # Record the previous state period
            duration = recorded_time - state_start_time
            minutes = duration.total_seconds() / 60
            
            if date_key in days:
                days[date_key].append({
                    'time': minutes,
                    'label': _format_label(
                        current_state,
                        duration,
                        state_start_time,
                        recorded_time
                    ),
                    'state': current_state
                })
            
            # Start new state
            current_state = new_state
            state_start_time = recorded_time
    
    # Handle the final state period
    if state_start_time:
        end_time = timezone.localtime(last_reading.recorded_at)
        duration = end_time - state_start_time
        minutes = duration.total_seconds() / 60
        date_key = end_time.date().isoformat()
        
        if date_key in days:
            days[date_key].append({
                'time': minutes,
                'label': _format_label(
                    current_state,
                    duration,
                    state_start_time,
                    end_time
                ),
                'state': current_state
            })
    
    # Create dates for x-axis
    dates = []
    for time in list(days.keys()):
        dates.append("{} 12:00:00".format(time))
    
    traces = []
    
    # Set iterator and determine maximum iteration for dates
    i = 0
    max_i = 0
    for date_times in days.values():
        max_i = max(len(date_times), max_i)
    
    while i < max_i:
        y = {}
        text = {}
        colors_list = {}
        
        for date in days.keys():
            try:
                y[date] = days[date][i]['time']
                text[date] = days[date][i]['label']
                colors_list[date] = ASLEEP_COLOR if days[date][i]['state'] == 'asleep' else AWAKE_COLOR
            except IndexError:
                y[date] = None
                text[date] = None
                colors_list[date] = AWAKE_COLOR
        
        # Use the first non-None color for this trace
        trace_color = next((c for c in colors_list.values() if c), AWAKE_COLOR)
        
        traces.append(
            go.Bar(
                x=dates,
                y=list(y.values()),
                hovertext=list(text.values()),
                hoverinfo="text",
                marker={"color": trace_color},
                showlegend=False,
            )
        )
        i += 1
    
    layout_args = utils.default_graph_layout_options()
    layout_args["margin"]["b"] = 100
    layout_args["barmode"] = "stack"
    layout_args["bargap"] = 0
    layout_args["hovermode"] = "closest"
    layout_args["title"] = "<b>" + _("Owlet Sleep/Wake Pattern") + "</b>"
    layout_args["height"] = 800
    
    layout_args["xaxis"]["title"] = _("Date")
    layout_args["xaxis"]["tickangle"] = -65
    layout_args["xaxis"]["tickformat"] = "%b %e\n%Y"
    layout_args["xaxis"]["ticklabelmode"] = "period"
    layout_args["xaxis"]["rangeselector"] = utils.rangeselector_date()
    
    start = timezone.localtime().strptime("12:00 AM", "%I:%M %p")
    ticks = OrderedDict()
    ticks[0] = start.strftime("%I:%M %p")
    for i in range(0, 60 * 24, 30):
        ticks[i] = formats.time_format(
            start + timezone.timedelta(minutes=i), "TIME_FORMAT"
        )
    
    layout_args["yaxis"]["title"] = _("Time of day")
    layout_args["yaxis"]["range"] = [24 * 60, 0]
    layout_args["yaxis"]["tickmode"] = "array"
    layout_args["yaxis"]["tickvals"] = list(ticks.keys())
    layout_args["yaxis"]["ticktext"] = list(ticks.values())
    layout_args["yaxis"]["tickfont"] = {"size": 10}
    
    fig = go.Figure({"data": traces, "layout": go.Layout(**layout_args)})
    output = plotly.plot(fig, output_type="div", include_plotlyjs=False)
    return utils.split_graph_output(output)


def _init_days(first_day, last_day):
    """Initialize dictionary of days for the date range."""
    period = (last_day.date() - first_day.date()).days + 1
    
    def new_day(d):
        return (first_day + timedelta(days=d)).date().isoformat()
    
    return {new_day(day): [] for day in range(period)}


def _format_label(state, duration, start_time, end_time):
    """
    Format a time block label for sleep/wake state.
    :param state: 'asleep' or 'awake'
    :param duration: Duration timedelta.
    :param start_time: Start time.
    :param end_time: End time.
    :return: Formatted string with duration, start, and end time.
    """
    hours = int(duration.total_seconds() // 3600)
    minutes = int((duration.total_seconds() % 3600) // 60)
    duration_str = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
    
    state_label = _("Asleep") if state == 'asleep' else _("Awake")
    
    return "{} {} ({} to {})".format(
        state_label,
        duration_str,
        formats.time_format(start_time, "TIME_FORMAT"),
        formats.time_format(end_time, "TIME_FORMAT"),
    )
