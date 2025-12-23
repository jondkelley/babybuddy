# Owlet Dashboard Card Implementation

## Overview
Added an Owlet Vitals card to the child dashboard that displays real-time heart rate, oxygen saturation, movement, and battery data from the Owlet smart sock.

## Features

### Real-Time Vitals Display
The card shows:
- **Heart Rate** (bpm)
- **Oxygen Saturation** (%)
- **Movement** (value)
- **Battery** (%)

### Stale Data Warning
If the reading is older than 60 seconds, the card displays **"STALE DATA"** in red text and dims the values. This helps you quickly identify when the Owlet sock may be disconnected or not transmitting.

### Auto-Refresh
The dashboard automatically refreshes based on your user settings (default: every 60 seconds), so the Owlet vitals stay up-to-date without manual page reloads.

## Files Created

1. **[`dashboard/templatetags/owlet_cards.py`](dashboard/templatetags/owlet_cards.py)** - Template tag function that fetches the latest Owlet reading and checks if it's stale

2. **[`dashboard/templates/cards/owlet_vitals.html`](dashboard/templates/cards/owlet_vitals.html)** - Card template that displays the vitals in a clean, organized layout

## Files Modified

1. **[`dashboard/templates/dashboard/child.html`](dashboard/templates/dashboard/child.html)** - Added the Owlet card to the dashboard (positioned after the timer list)

## Database Fields

The movement fields already existed in the [`OwletReading`](owlet/models.py:41) model:
- `movement_value` - Current movement reading
- `movement_baseline` - Baseline movement value

These are now displayed in the dashboard card.

## Usage

1. Navigate to a child's dashboard: http://localhost:8001/children/{child-slug}/dashboard/
2. The Owlet Vitals card will appear near the top of the dashboard
3. If no readings exist yet, it will show "No readings yet"
4. If readings are older than 60 seconds, "STALE DATA" will be displayed in red
5. Click the "Owlet Vitals" header to go to the Owlet settings page

## Stale Data Logic

The card checks the age of the reading:
```python
age = timezone.now() - instance.recorded_at
stale = age.total_seconds() > 60
```

Since the poller runs every 30 seconds, readings should never be more than 30-40 seconds old under normal operation. If they're older than 60 seconds, it indicates:
- The Owlet sock is not being worn
- The sock is out of range
- The polling service has stopped
- Network connectivity issues

## Next Steps

To see live data in the card:
1. Ensure the Owlet device is mapped to a child
2. Put the Owlet sock on the baby
3. Wait for the next poll cycle (max 30 seconds)
4. The dashboard will auto-refresh and show the latest vitals
