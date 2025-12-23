# Owlet Reports Implementation

This document describes the new Owlet-based reports that have been added to Baby Buddy, providing doctors and parents with valuable insights into baby health data collected from Owlet devices.

## Overview

Four new reports have been added to the Baby Buddy reporting system, leveraging data from Owlet smart sock devices. These reports use the same technology stack as existing reports (Plotly.js for visualization) and follow the established patterns in the codebase.

## New Reports

### 1. Owlet Heart Rate Report
**File:** [`reports/graphs/owlet_heart_rate.py`](reports/graphs/owlet_heart_rate.py)  
**URL:** `/children/<slug>/reports/owlet/heart-rate/`  
**Template:** [`reports/templates/reports/owlet_heart_rate.html`](reports/templates/reports/owlet_heart_rate.html)

**Features:**
- Line graph showing heart rate readings over time
- Normal range indicators (80-180 bpm for infants)
- Interactive hover tooltips with exact BPM and timestamp
- Time-based range selectors (12h, 24h, 48h, 3d, 7d, all)
- Y-axis range: 60-200 bpm

**Medical Relevance:**
- Monitors baby's cardiovascular health
- Helps identify bradycardia (low heart rate) or tachycardia (high heart rate)
- Tracks heart rate patterns during sleep and wake cycles

### 2. Owlet Oxygen Saturation Report
**File:** [`reports/graphs/owlet_oxygen.py`](reports/graphs/owlet_oxygen.py)  
**URL:** `/children/<slug>/reports/owlet/oxygen/`  
**Template:** [`reports/templates/reports/owlet_oxygen.html`](reports/templates/reports/owlet_oxygen.html)

**Features:**
- Line graph showing oxygen saturation percentage over time
- Normal range indicator (95% threshold)
- Alert threshold indicator (80% - Owlet's default alert level)
- Interactive hover tooltips with exact percentage and timestamp
- Time-based range selectors
- Y-axis range: 75-100%

**Medical Relevance:**
- Critical for monitoring respiratory health
- Helps detect hypoxemia (low blood oxygen)
- Essential for babies with respiratory conditions or sleep apnea
- Normal range: 95-100%

### 3. Owlet Sleep/Wake Pattern Report
**File:** [`reports/graphs/owlet_sleep_pattern.py`](reports/graphs/owlet_sleep_pattern.py)  
**URL:** `/children/<slug>/reports/owlet/sleep-pattern/`  
**Template:** [`reports/templates/reports/owlet_sleep_pattern.html`](reports/templates/reports/owlet_sleep_pattern.html)

**Features:**
- Stacked bar chart showing sleep/wake periods throughout each day
- Uses movement data to infer sleep state (movement < 30 = asleep)
- Color-coded: Blue for asleep, Orange for awake
- Shows time of day on Y-axis (24-hour format)
- Date range selectors (1w, 2w, 1m, 3m, all)
- Interactive hover showing duration and time range for each period

**Medical Relevance:**
- Visualizes sleep patterns and circadian rhythm development
- Helps identify sleep disturbances or irregular patterns
- Useful for tracking sleep training progress
- Can reveal correlations with feeding, health issues, or environmental factors

### 4. Owlet Sleep Totals Report
**File:** [`reports/graphs/owlet_sleep_totals.py`](reports/graphs/owlet_sleep_totals.py)  
**URL:** `/children/<slug>/reports/owlet/sleep-totals/`  
**Template:** [`reports/templates/reports/owlet_sleep_totals.html`](reports/templates/reports/owlet_sleep_totals.html)

**Features:**
- Bar chart showing total sleep hours per day
- Calculated from movement data (movement < 30 indicates sleep)
- Hover tooltips showing hours and minutes
- Date range selectors
- Complements the existing manual Sleep Totals report

**Medical Relevance:**
- Tracks overall sleep quantity
- Helps ensure baby is getting adequate rest
- Can identify trends in sleep duration
- Useful for comparing with recommended sleep amounts for age

## Technical Implementation

### Technology Stack
- **Visualization:** Plotly.js (same as existing reports)
- **Backend:** Django class-based views with `PermissionRequiredMixin`
- **Data Source:** `OwletReading` model from [`owlet/models.py`](owlet/models.py)
- **Styling:** Consistent with existing reports (dark theme, responsive)

### Key Files Modified/Created

**Graph Modules:**
- [`reports/graphs/owlet_heart_rate.py`](reports/graphs/owlet_heart_rate.py)
- [`reports/graphs/owlet_oxygen.py`](reports/graphs/owlet_oxygen.py)
- [`reports/graphs/owlet_sleep_pattern.py`](reports/graphs/owlet_sleep_pattern.py)
- [`reports/graphs/owlet_sleep_totals.py`](reports/graphs/owlet_sleep_totals.py)
- [`reports/graphs/__init__.py`](reports/graphs/__init__.py) - Updated to export new functions

**Views:**
- [`reports/views.py`](reports/views.py) - Added 4 new view classes:
  - `OwletHeartRateChildReport`
  - `OwletOxygenChildReport`
  - `OwletSleepPatternChildReport`
  - `OwletSleepTotalsChildReport`

**URLs:**
- [`reports/urls.py`](reports/urls.py) - Added 4 new URL patterns

**Templates:**
- [`reports/templates/reports/owlet_heart_rate.html`](reports/templates/reports/owlet_heart_rate.html)
- [`reports/templates/reports/owlet_oxygen.html`](reports/templates/reports/owlet_oxygen.html)
- [`reports/templates/reports/owlet_sleep_pattern.html`](reports/templates/reports/owlet_sleep_pattern.html)
- [`reports/templates/reports/owlet_sleep_totals.html`](reports/templates/reports/owlet_sleep_totals.html)
- [`reports/templates/reports/report_list.html`](reports/templates/reports/report_list.html) - Updated to include Owlet reports

## Data Requirements

All reports require:
- An Owlet account configured in the system
- An Owlet device mapped to the child
- Owlet readings collected via the polling service

The reports will show a "not enough data" message if no readings are available.

## Sleep Detection Algorithm

The sleep/wake pattern and sleep totals reports use a simple but effective algorithm:
- **Movement Threshold:** 30 (configurable in code)
- **Logic:** `movement_value < 30` = asleep, `>= 30` = awake
- **Rationale:** Lower movement values indicate the baby is still/sleeping

This threshold can be adjusted based on real-world testing and feedback.

## Integration with Existing Reports

The Owlet reports complement existing manual tracking reports:
- **Sleep Pattern:** Owlet version uses continuous movement data vs. manual sleep entries
- **Sleep Totals:** Owlet version provides automated tracking vs. manual entries
- Both can be used together for comprehensive sleep analysis

## Medical Use Cases

These reports are particularly valuable for:
1. **Routine Monitoring:** Track overall health trends
2. **Medical Consultations:** Provide objective data to pediatricians
3. **Respiratory Issues:** Monitor oxygen levels for babies with breathing concerns
4. **Sleep Problems:** Analyze sleep patterns for babies with sleep difficulties
5. **Post-Hospital Care:** Track recovery after medical procedures
6. **Developmental Tracking:** Observe how vital signs change as baby grows

## Future Enhancements

Potential improvements:
- Add movement intensity report
- Correlate heart rate with sleep states
- Add alert history visualization
- Export reports as PDF for doctor visits
- Add statistical analysis (averages, trends, anomalies)
- Configurable thresholds for sleep detection
- Integration with manual sleep entries for hybrid tracking

## Related Documentation

- [`OWLET_API_FIELDS.md`](OWLET_API_FIELDS.md) - Complete Owlet API field documentation
- [`OWLET_DASHBOARD_CARD.md`](OWLET_DASHBOARD_CARD.md) - Dashboard card implementation
- [`OWLET_POLLING_FIX.md`](OWLET_POLLING_FIX.md) - Polling service documentation
- [`owlet/models.py`](owlet/models.py) - Owlet data models
