# Owlet API Field Documentation

This document provides comprehensive documentation for all fields returned by the Owlet Baby Monitor API.

## Table of Contents

- [Vital Signs & Measurements](#vital-signs--measurements)
- [Battery & Power](#battery--power)
- [Connection & Signal Quality](#connection--signal-quality)
- [Status Codes](#status-codes)
- [Alerts & Monitoring](#alerts--monitoring)
- [System & Hardware](#system--hardware)
- [Example Data](#example-data)

## Vital Signs & Measurements

### `hr` (heart_rate_bpm)
**Heart rate in beats per minute**

- **Type:** Integer
- **Range:** 0-255 (typical infant: 80-180 bpm)
- **Normal resting:** 100-160 bpm
- **Example:** `130`

### `ox` (oxygen_saturation_pct)
**Blood oxygen saturation percentage**

- **Type:** Integer
- **Range:** 0-100%
- **Normal range:** 95-100%
- **Alert threshold:** Owlet typically alerts below 80%
- **Example:** `90`

### `mv` (movement_value)
**Current movement reading**

- **Type:** Integer
- **Range:** 0-255
- **Description:** Higher values indicate more movement
- **Example:** `36`

### `mvb` (movement_baseline)
**Movement baseline for comparison**

- **Type:** Integer
- **Range:** 0-255
- **Description:** Used to detect significant movement changes from baseline
- **Example:** `50`

### `oxta` (oxygen_target_pct)
**Oxygen saturation alert threshold**

- **Type:** Integer
- **Range:** 0-100% (255 may indicate "not set")
- **Description:** The oxygen level below which alerts are triggered
- **Example:** `255` (not set)

## Battery & Power

### `bat` (battery_pct)
**Battery charge percentage**

- **Type:** Integer
- **Range:** 0-100%
- **Example:** `77`

### `btt` (battery_temp_tenths_c)
**Battery temperature in tenths of degrees Celsius**

- **Type:** Integer
- **Range:** 0-1000+ (divide by 10 to get actual temperature)
- **Description:** Battery temperature monitoring for safety
- **Example:** `750` (= 75.0°C)

### `chg` (charging)
**Charging status**

- **Type:** Boolean (0 or 1)
- **Values:**
  - `0` = not charging
  - `1` = charging
- **Example:** `0`

### `bp` (base_power_state_code)
**Base station power state**

- **Type:** Integer
- **Values:**
  - `0` = off/unpowered
  - `1` = on/powered
- **Example:** `1`

## Connection & Signal Quality

### `sc` (sock_connection_state_code)
**Sock connection state**

- **Type:** Integer
- **Values:**
  - `0` = disconnected
  - `1` = connecting
  - `2` = connected
- **Example:** `2`

### `rsi` (signal_quality)
**WiFi/Bluetooth signal strength indicator**

- **Type:** Integer
- **Range:** 0-100 (higher is better)
- **Description:** Signal quality between sock and base station
- **Example:** `43`

### `srf` (sensor_readiness_flag_code)
**Sensor readiness status**

- **Type:** Integer
- **Range:** 0-3
- **Description:** Indicates sensor calibration/readiness state (exact meanings not fully documented)
- **Example:** `3`

## Status Codes

### `st` (state_code)
**Overall device state**

- **Type:** Integer
- **Description:** Numeric status indicator (exact meanings not fully documented by Owlet)
- **Example:** `34`

### `ss` (sock_status_code)
**Sock-specific status**

- **Type:** Integer
- **Description:** Numeric status indicator for sock-specific states
- **Example:** `0`

### `sb` (sock_battery_status_code)
**Sock battery status**

- **Type:** Integer
- **Values:**
  - `0` = normal
  - Other values may indicate warnings/errors
- **Example:** `0`

### `bsb` (base_status_code)
**Base station status**

- **Type:** Integer
- **Description:** Numeric status indicator for base station
- **Example:** `0`

### `bso` (base_socket_occupied)
**Whether sock is docked in base station**

- **Type:** Boolean (0 or 1)
- **Values:**
  - `0` = sock not in base (on baby or elsewhere)
  - `1` = sock in base station
- **Example:** `0`

## Alerts & Monitoring

### `alrt` (alert_state_code)
**Active alert state**

- **Type:** Integer
- **Values:**
  - `0` = no alert
  - Other values indicate specific alert types (heart rate, oxygen, disconnection, etc.)
- **Example:** `0`

### `aps` (alert_pause_status)
**Whether alerts are paused**

- **Type:** Boolean (0 or 1)
- **Values:**
  - `0` = alerts active
  - `1` = alerts paused
- **Example:** `0`

### `mrs` (monitoring_state_code)
**Monitoring state**

- **Type:** Integer
- **Values:**
  - `0` = not monitoring
  - `1` = actively monitoring
- **Example:** `1`

### `onm` (operation_mode)
**Device operation mode**

- **Type:** Integer
- **Range:** 0-3
- **Description:** Indicates different operational states (exact meanings not fully documented)
- **Example:** `3`

## System & Hardware

### `hw` (hardware_model)
**Hardware model identifier**

- **Type:** String
- **Values:**
  - `"obs3"` = Owlet Baby Sock 3
  - `"obs4"` = Owlet Baby Sock 4
- **Example:** `"obs4"`

### `ota` (ota_status_code)
**Over-the-air firmware update status**

- **Type:** Integer
- **Values:**
  - `0` = no update in progress
  - `1` = update in progress
- **Example:** `0`

### `mst` (measurement_timestamp_epoch)
**Unix timestamp of measurement**

- **Type:** Integer/Float
- **Description:** Seconds since Unix epoch (1970-01-01 00:00:00 UTC)
- **Note:** `0` may indicate timestamp not set
- **Example:** `0` or `1703289600`

## Example Data

Here's a complete example of data returned by the Owlet API:

```json
{
  "ox": 90,
  "hr": 130,
  "mv": 36,
  "sc": 2,
  "st": 34,
  "bso": 0,
  "bat": 77,
  "btt": 750,
  "chg": 0,
  "aps": 0,
  "alrt": 0,
  "ota": 0,
  "srf": 3,
  "rsi": 43,
  "sb": 0,
  "ss": 0,
  "mvb": 50,
  "mst": 0,
  "oxta": 255,
  "onm": 3,
  "bsb": 0,
  "mrs": 1,
  "bp": 1,
  "hw": "obs4"
}
```

### Interpretation of Example Data

- **Baby is being actively monitored** (`mrs`: 1)
- **Sock is connected** (`sc`: 2)
- **Oxygen saturation at 90%** - Lower end of normal range
- **Heart rate at 130 bpm** - Normal for an infant
- **Battery at 77%**, not charging
- **Good signal quality** (`rsi`: 43)
- **No active alerts** (`alrt`: 0, `aps`: 0)
- **Using Owlet Sock 4 hardware** (`hw`: "obs4")
- **Sock is on baby** (not in base station, `bso`: 0)
- **Base station is powered on** (`bp`: 1)

## Field Mapping Reference

The following table shows the mapping between abbreviated API field names and their descriptive names:

| API Field | Descriptive Name | Category |
|-----------|------------------|----------|
| `hr` | heart_rate_bpm | Vital Signs |
| `ox` | oxygen_saturation_pct | Vital Signs |
| `mv` | movement_value | Vital Signs |
| `mvb` | movement_baseline | Vital Signs |
| `oxta` | oxygen_target_pct | Vital Signs |
| `bat` | battery_pct | Battery & Power |
| `btt` | battery_temp_tenths_c | Battery & Power |
| `chg` | charging | Battery & Power |
| `bp` | base_power_state_code | Battery & Power |
| `sc` | sock_connection_state_code | Connection |
| `rsi` | signal_quality | Connection |
| `srf` | sensor_readiness_flag_code | Connection |
| `st` | state_code | Status |
| `ss` | sock_status_code | Status |
| `sb` | sock_battery_status_code | Status |
| `bsb` | base_status_code | Status |
| `bso` | base_socket_occupied | Status |
| `alrt` | alert_state_code | Alerts |
| `aps` | alert_pause_status | Alerts |
| `mrs` | monitoring_state_code | Alerts |
| `onm` | operation_mode | Alerts |
| `hw` | hardware_model | System |
| `ota` | ota_status_code | System |
| `mst` | measurement_timestamp_epoch | System |

## Implementation Notes

- Many numeric status codes are not fully documented by Owlet's official API documentation
- Fields with `_code` suffix are treated as numeric indicators where exact meanings may vary
- Boolean fields (`chg`, `bso`) are represented as integers (0 or 1) in the API
- The `btt` field requires division by 10 to get the actual temperature in Celsius
- Some fields may not be present in all API responses depending on device state and firmware version

## Related Files

- [`pyowletapi/get_metrics.py`](pyowletapi/get_metrics.py) - Detailed field mapping implementation
- [`babybuddy/services/owlet_poll.py`](babybuddy/services/owlet_poll.py) - Polling service using these mappings
- [`owlet/models.py`](owlet/models.py) - Database models for storing Owlet readings
