
import asyncio
import os
import json
from datetime import datetime, timezone
from pprint import pformat
from pyowletapi.api import OwletAPI


def _pretty_json(obj) -> str:
    """Return a nicely formatted string for dicts/lists/JSON-like values."""
    try:
        return json.dumps(obj, indent=2, sort_keys=True)
    except (TypeError, ValueError):
        # Fallback for non-JSON-serializable objects
        return pformat(obj, indent=2, width=120, sort_dicts=True)


def _parse_json_if_str(value):
    """If value is a JSON string, parse it to a dict; otherwise return as-is."""
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


# Owlet API Field Mappings and Documentation
# ============================================
# This mapping translates abbreviated Owlet API field names to descriptive names.
# For ambiguous numeric flags, we keep a *_code suffix to avoid mislabeling.
#
# VITAL SIGNS & MEASUREMENTS:
# ---------------------------
# hr  (heart_rate_bpm): Heart rate in beats per minute
#     - Typical infant range: 80-180 bpm
#     - Normal resting: 100-160 bpm
#     - Example: 130
#
# ox  (oxygen_saturation_pct): Blood oxygen saturation percentage
#     - Normal range: 95-100%
#     - Owlet alerts typically trigger below 80%
#     - Example: 90
#
# mv  (movement_value): Current movement reading
#     - Range: 0-255
#     - Higher values indicate more movement
#     - Example: 36
#
# mvb (movement_baseline): Movement baseline for comparison
#     - Range: 0-255
#     - Used to detect significant movement changes
#     - Example: 50
#
# oxta (oxygen_target_pct): Oxygen saturation alert threshold
#     - Range: 0-100% (255 may indicate "not set")
#     - Example: 255
#
# BATTERY & POWER:
# ----------------
# bat (battery_pct): Battery charge percentage
#     - Range: 0-100%
#     - Example: 77
#
# btt (battery_temp_tenths_c): Battery temperature in tenths of degrees Celsius
#     - Divide by 10 to get actual temperature
#     - Example: 750 = 75.0°C
#
# chg (charging): Charging status
#     - 0 = not charging
#     - 1 = charging
#     - Example: 0
#
# bp  (base_power_state_code): Base station power state
#     - 0 = off/unpowered
#     - 1 = on/powered
#     - Example: 1
#
# CONNECTION & SIGNAL QUALITY:
# ----------------------------
# sc  (sock_connection_state_code): Sock connection state
#     - 0 = disconnected
#     - 1 = connecting
#     - 2 = connected
#     - Example: 2
#
# rsi (signal_quality): WiFi/Bluetooth signal strength indicator
#     - Range: 0-100 (higher is better)
#     - Example: 43
#
# srf (sensor_readiness_flag_code): Sensor readiness status
#     - Range: 0-3 (exact meanings not fully documented)
#     - Likely indicates sensor calibration/readiness state
#     - Example: 3
#
# STATUS CODES:
# -------------
# st  (state_code): Overall device state
#     - Numeric status indicator (exact meanings not fully documented)
#     - Example: 34
#
# ss  (sock_status_code): Sock-specific status
#     - Numeric status indicator
#     - Example: 0
#
# sb  (sock_battery_status_code): Sock battery status
#     - 0 = normal
#     - Other values may indicate warnings/errors
#     - Example: 0
#
# bsb (base_status_code): Base station status
#     - Numeric status indicator
#     - Example: 0
#
# bso (base_socket_occupied): Whether sock is docked in base station
#     - 0 = sock not in base (on baby or elsewhere)
#     - 1 = sock in base station
#     - Example: 0
#
# ALERTS & MONITORING:
# --------------------
# alrt (alert_state_code): Active alert state
#     - 0 = no alert
#     - Other values indicate specific alert types (heart rate, oxygen, etc.)
#     - Example: 0
#
# aps (alert_pause_status): Whether alerts are paused
#     - 0 = alerts active
#     - 1 = alerts paused
#     - Example: 0
#
# mrs (monitoring_state_code): Monitoring state
#     - 0 = not monitoring
#     - 1 = actively monitoring
#     - Example: 1
#
# onm (operation_mode): Device operation mode
#     - Range: 0-3 (exact meanings not fully documented)
#     - Likely indicates different operational states
#     - Example: 3
#
# SYSTEM & HARDWARE:
# ------------------
# hw  (hardware_model): Hardware model identifier
#     - Examples: "obs3" (Owlet Baby Sock 3), "obs4" (Owlet Baby Sock 4)
#     - Example: "obs4"
#
# ota (ota_status_code): Over-the-air firmware update status
#     - 0 = no update in progress
#     - 1 = update in progress
#     - Example: 0
#
# mst (measurement_timestamp_epoch): Unix timestamp of measurement
#     - Seconds since Unix epoch (1970-01-01)
#     - 0 may indicate timestamp not set
#     - Example: 0
#
# EXAMPLE DATA:
# -------------
# {
#   "ox": 90,    # 90% oxygen saturation
#   "hr": 130,   # 130 beats per minute
#   "mv": 36,    # Movement value of 36
#   "sc": 2,     # Connected
#   "st": 34,    # State code 34
#   "bso": 0,    # Not in base station
#   "bat": 77,   # 77% battery
#   "btt": 750,  # 75.0°C battery temperature
#   "chg": 0,    # Not charging
#   "aps": 0,    # Alerts not paused
#   "alrt": 0,   # No active alerts
#   "ota": 0,    # No OTA update
#   "srf": 3,    # Sensor readiness flag 3
#   "rsi": 43,   # Signal quality 43
#   "sb": 0,     # Sock battery status normal
#   "ss": 0,     # Sock status 0
#   "mvb": 50,   # Movement baseline 50
#   "mst": 0,    # Timestamp not set
#   "oxta": 255, # Oxygen target not set
#   "onm": 3,    # Operation mode 3
#   "bsb": 0,    # Base status 0
#   "mrs": 1,    # Actively monitoring
#   "bp": 1,     # Base powered on
#   "hw": "obs4" # Owlet Baby Sock 4
# }

KEY_MAP: dict[str, str] = {
    # Clear metrics
    "hr": "heart_rate_bpm",
    "ox": "oxygen_saturation_pct",
    "oxta": "oxygen_target_pct",
    "bat": "battery_pct",
    "chg": "charging",
    "mv": "movement_value",
    "mvb": "movement_baseline",
    "rsi": "signal_quality",
    "hw": "hardware_model",
    "mst": "measurement_timestamp_epoch",
    "onm": "operation_mode",
    # Likely alert/pause/ota states
    "aps": "alert_pause_status",
    "alrt": "alert_state_code",
    "ota": "ota_status_code",
    # Sock/base/sensor status fields (treated as codes)
    "sb": "sock_battery_status_code",
    "sc": "sock_connection_state_code",
    "ss": "sock_status_code",
    "st": "state_code",
    "bp": "base_power_state_code",
    "bso": "base_socket_occupied",
    "bsb": "base_status_code",
    "srf": "sensor_readiness_flag_code",
    # Temperature-ish (tenths of degree C) – label conservatively
    "btt": "battery_temp_tenths_c",
    # Monitoring state
    "mrs": "monitoring_state_code",
}


def _rename_vitals(v: dict) -> dict:
    if not isinstance(v, dict):
        return v
    out: dict = {}
    for k, val in v.items():
        new_key = KEY_MAP.get(k, k)
        out[new_key] = val

    # Post-process booleans where appropriate
    if "charging" in out:
        out["charging"] = bool(out["charging"])
    if "base_socket_occupied" in out:
        out["base_socket_occupied"] = bool(out["base_socket_occupied"])

    # Add ISO timestamp for convenience if epoch is present
    if isinstance(out.get("measurement_timestamp_epoch"), (int, float)):
        try:
            out["measurement_timestamp_iso"] = datetime.fromtimestamp(
                out["measurement_timestamp_epoch"], tz=timezone.utc
            ).isoformat()
        except Exception:
            pass

    return out

async def get_owlet_data():
    # Get credentials from environment variables
    username = os.environ.get("OWLET_USERNAME")
    password = os.environ.get("OWLET_PASSWORD")

    if not username or not password:
        print("OWLET_USERNAME and OWLET_PASSWORD environment variables must be set.")
        return

    # Monkey-patch the OwletAPI class
    async def aenter(self):
        await self.authenticate()
        return self

    async def aexit(self, exc_type, exc, tb):
        await self.close()

    async def get_live_values(self, dsn):
        properties = await self.get_properties(dsn)
        print('DEBUG: properties from get_properties:\n' + _pretty_json(properties))
        resp = properties.get('response', properties)

        # If response is a list, search for REAL_TIME_VITALS dict
        if isinstance(resp, list):
            for entry in resp:
                if 'REAL_TIME_VITALS' in entry:
                    vitals = entry['REAL_TIME_VITALS']
                    break
            else:
                raise Exception('REAL_TIME_VITALS key not found in response list')
        elif isinstance(resp, dict):
            if 'REAL_TIME_VITALS' in resp:
                vitals = resp['REAL_TIME_VITALS']
            else:
                raise Exception('REAL_TIME_VITALS key not found in response dict')
        else:
            raise Exception('Unexpected response type: %s' % type(resp))

        # REAL_TIME_VITALS is typically provided as a JSON string in the 'value' field
        raw_val = vitals.get('value') if isinstance(vitals, dict) else vitals
        parsed = _parse_json_if_str(raw_val)
        if isinstance(parsed, (dict, list)):
            return parsed
        raise Exception('Could not extract value for REAL_TIME_VITALS: ' + str(vitals))

    OwletAPI.__aenter__ = aenter
    OwletAPI.__aexit__ = aexit
    OwletAPI.get_live_values = get_live_values

    async with OwletAPI("world", username, password) as owlet:
        # Get all devices
        devices = await owlet.get_devices()
        print('Devices response:\n' + _pretty_json(devices))

        # Handle response wrapping
        if isinstance(devices, dict) and 'response' in devices:
            resp = devices['response']
        elif isinstance(devices, list) and len(devices) > 0 and 'response' in devices[0]:
            resp = devices[0]['response']
        else:
            resp = devices

        # Most likely resp is a list of device dicts
        if isinstance(resp, list) and resp:
            device = resp[0].get('device', resp[0])
        elif isinstance(resp, dict) and 'device' in resp:
            device = resp['device']
        elif isinstance(resp, dict):
            device = resp
        else:
            print("Could not parse devices structure:", devices)
            return

        if not device or not device.get("dsn"):
            print("No device with 'dsn' found:", device)
            return

        # Get live values
        try:
            live_values = await owlet.get_live_values(device['dsn'])
            print('Live values (parsed):\n' + _pretty_json(live_values))

            renamed = _rename_vitals(live_values)
            print('Live values (renamed):\n' + _pretty_json(renamed))

            # Some firmwares use abbreviated keys (hr/ox). Prefer long names if present.
            hr = (
                live_values.get('heart_rate')
                if isinstance(live_values, dict) else None
            )
            if hr is None and isinstance(live_values, dict):
                hr = live_values.get('hr')

            ox = (
                live_values.get('oxygen_level')
                if isinstance(live_values, dict) else None
            )
            if ox is None and isinstance(live_values, dict):
                ox = live_values.get('ox')

            if hr is not None:
                print(f"Heart Rate (BPM): {hr}")
            if ox is not None:
                print(f"Oxygen Level: {ox}%")
        except Exception as e:
            print(f"Could not get live values: {e}")


if __name__ == "__main__":
    asyncio.run(get_owlet_data())
