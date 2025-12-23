# -*- coding: utf-8 -*-
from datetime import timedelta
from django import template
from django.utils import timezone
from django.utils.translation import gettext as _

from owlet.models import OwletReading

register = template.Library()


def _hide_empty(context):
    return context["request"].user.settings.dashboard_hide_empty


def _get_child_age_months(child):
    """Calculate child's age in months."""
    if not child.birth_date:
        return None
    today = timezone.localdate()
    age_days = (today - child.birth_date).days
    age_months = age_days / 30.44  # Average days per month
    return age_months


def _determine_awake_status(reading):
    """Determine if child is awake based on movement data."""
    if reading.movement_value is None or reading.movement_baseline is None:
        return None
    
    # If movement is significantly higher than baseline, likely awake
    if reading.movement_value > reading.movement_baseline * 1.5:
        return True
    return False


def _check_heart_rate_normal(heart_rate, age_months, is_awake):
    """Check if heart rate is within normal range for age."""
    if heart_rate is None or age_months is None:
        return True  # Can't determine, assume normal
    
    if is_awake:
        # Waking pulse rates
        if age_months < 4:  # 1-3 months
            return 100 <= heart_rate <= 205
        elif age_months < 12:  # 4-12 months
            return 100 <= heart_rate <= 180
        elif age_months < 24:  # 1-2 years
            return 98 <= heart_rate <= 140
        elif age_months < 60:  # 3-5 years
            return 80 <= heart_rate <= 120
        else:
            return True  # Beyond 5 years, assume normal
    else:
        # Sleeping pulse rates
        if age_months < 4:  # 1-3 months
            return 90 <= heart_rate <= 160
        elif age_months < 12:  # 4-12 months
            return 90 <= heart_rate <= 160
        elif age_months < 24:  # 1-2 years
            return 80 <= heart_rate <= 120
        elif age_months < 60:  # 3-5 years
            return 60 <= heart_rate <= 100
        else:
            return True  # Beyond 5 years, assume normal


@register.inclusion_tag("cards/owlet_vitals.html", takes_context=True)
def card_owlet_vitals(context, child):
    """
    Information about the most recent Owlet vitals reading.
    :param child: an instance of the Child model.
    :returns: a dictionary with the most recent OwletReading instance.
    """
    instance = (
        OwletReading.objects.filter(child=child)
        .order_by("-recorded_at")
        .first()
    )
    empty = not instance
    
    # Check if data is stale (older than 60 seconds)
    stale = False
    if instance:
        age = timezone.now() - instance.recorded_at
        stale = age.total_seconds() > 60

    return {
        "type": "owlet",
        "reading": instance,
        "stale": stale,
        "empty": empty,
        "hide_empty": _hide_empty(context),
    }


@register.inclusion_tag("cards/owlet_heart_rate.html", takes_context=True)
def card_owlet_heart_rate(context, child):
    """
    Information about the most recent Owlet heart rate reading.
    :param child: an instance of the Child model.
    :returns: a dictionary with heart rate data and validation.
    """
    instance = (
        OwletReading.objects.filter(child=child)
        .order_by("-recorded_at")
        .first()
    )
    empty = not instance
    
    # Check if data is stale (older than 60 seconds)
    stale = False
    alert = False
    is_awake = None
    
    if instance:
        age = timezone.now() - instance.recorded_at
        stale = age.total_seconds() > 60
        
        # Determine awake status
        is_awake = _determine_awake_status(instance)
        
        # Check if heart rate is normal for age
        age_months = _get_child_age_months(child)
        if instance.heart_rate_bpm and age_months:
            alert = not _check_heart_rate_normal(instance.heart_rate_bpm, age_months, is_awake)

    return {
        "type": "owlet_heart_rate",
        "reading": instance,
        "stale": stale,
        "alert": alert,
        "is_awake": is_awake,
        "empty": empty,
        "hide_empty": _hide_empty(context),
    }


@register.inclusion_tag("cards/owlet_oxygen.html", takes_context=True)
def card_owlet_oxygen(context, child):
    """
    Information about the most recent Owlet oxygen saturation reading.
    :param child: an instance of the Child model.
    :returns: a dictionary with oxygen data and alert status.
    """
    instance = (
        OwletReading.objects.filter(child=child)
        .order_by("-recorded_at")
        .first()
    )
    empty = not instance
    
    # Check if data is stale (older than 60 seconds)
    stale = False
    alert = False
    
    if instance:
        age = timezone.now() - instance.recorded_at
        stale = age.total_seconds() > 60
        
        # Alert if oxygen is below 90%
        if instance.oxygen_saturation_pct and instance.oxygen_saturation_pct < 90:
            alert = True

    return {
        "type": "owlet_oxygen",
        "reading": instance,
        "stale": stale,
        "alert": alert,
        "empty": empty,
        "hide_empty": _hide_empty(context),
    }


@register.inclusion_tag("cards/owlet_consciousness.html", takes_context=True)
def card_owlet_consciousness(context, child):
    """
    Information about the child's consciousness state (Awake/Asleep).
    :param child: an instance of the Child model.
    :returns: a dictionary with consciousness state.
    """
    instance = (
        OwletReading.objects.filter(child=child)
        .order_by("-recorded_at")
        .first()
    )
    empty = not instance
    
    # Check if data is stale (older than 60 seconds)
    stale = False
    is_awake = None
    
    if instance:
        age = timezone.now() - instance.recorded_at
        stale = age.total_seconds() > 60
        
        # Determine awake status
        is_awake = _determine_awake_status(instance)

    return {
        "type": "owlet_consciousness",
        "reading": instance,
        "stale": stale,
        "is_awake": is_awake,
        "empty": empty,
        "hide_empty": _hide_empty(context),
    }
