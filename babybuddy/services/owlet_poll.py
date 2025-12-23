from __future__ import annotations

from typing import Any, Dict, List, Tuple
import asyncio
import logging

from django.db import transaction
from django.utils import timezone

from owlet.models import OwletAccount, OwletDevice, OwletReading
from babybuddy.services.owlet_client import OwletClient

logger = logging.getLogger(__name__)


# Owlet API Field Mappings and Documentation
# ============================================
# This mapping translates abbreviated Owlet API field names to descriptive names.
# See pyowletapi/get_metrics.py for detailed documentation of each field.
#
# Quick Reference:
# ----------------
# VITAL SIGNS:
#   hr  (heart_rate_bpm): 80-180 bpm typical for infants
#   ox  (oxygen_saturation_pct): 95-100% normal, alerts <80%
#   mv  (movement_value): 0-255 scale
#   mvb (movement_baseline): 0-255 scale
#   oxta (oxygen_target_pct): Alert threshold (255=not set)
#
# BATTERY & POWER:
#   bat (battery_pct): 0-100%
#   btt (battery_temp_tenths_c): Temperature in tenths of °C (750=75.0°C)
#   chg (charging): 0=no, 1=yes
#   bp  (base_power_state_code): 0=off, 1=on
#
# CONNECTION:
#   sc  (sock_connection_state_code): 0=disconnected, 1=connecting, 2=connected
#   rsi (signal_quality): 0-100 (higher is better)
#   srf (sensor_readiness_flag_code): 0-3 sensor status
#
# STATUS:
#   st  (state_code): Overall device state
#   ss  (sock_status_code): Sock-specific status
#   sb  (sock_battery_status_code): 0=normal
#   bsb (base_status_code): Base station status
#   bso (base_socket_occupied): 0=not in base, 1=in base
#
# ALERTS & MONITORING:
#   alrt (alert_state_code): 0=no alert, other=alert type
#   aps (alert_pause_status): 0=active, 1=paused
#   mrs (monitoring_state_code): 0=off, 1=monitoring
#   onm (operation_mode): 0-3 operational state
#
# SYSTEM:
#   hw  (hardware_model): "obs3", "obs4", etc.
#   ota (ota_status_code): 0=no update, 1=updating
#   mst (measurement_timestamp_epoch): Unix timestamp

KEY_MAP: dict[str, str] = {
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
    "aps": "alert_pause_status",
    "alrt": "alert_state_code",
    "ota": "ota_status_code",
    "sb": "sock_battery_status_code",
    "sc": "sock_connection_state_code",
    "ss": "sock_status_code",
    "st": "state_code",
    "bp": "base_power_state_code",
    "bso": "base_socket_occupied",
    "bsb": "base_status_code",
    "srf": "sensor_readiness_flag_code",
    "btt": "battery_temp_tenths_c",
    "mrs": "monitoring_state_code",
}


def _normalize_vitals(v: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for k, val in v.items():
        out[KEY_MAP.get(k, k)] = val
    if "charging" in out:
        out["charging"] = bool(out["charging"])
    return out


async def poll_all() -> dict[str, Any]:
    """Poll all active accounts/devices and persist readings."""
    results: dict[str, Any] = {"accounts": 0, "devices": 0, "readings": 0}
    async def handle_account(account: OwletAccount):
        nonlocal results
        async with OwletClient(account) as client:
            devices = await client.get_devices()
            results["accounts"] += 1
            for d in devices:
                dev = d.get("device", d)
                dsn = dev.get("dsn")
                name = dev.get("product_name") or dev.get("model") or dsn
                if not dsn:
                    continue
                obj, _ = OwletDevice.objects.get_or_create(
                    account=account,
                    dsn=dsn,
                    defaults={"name": name or dsn},
                )
                if name and obj.name != name:
                    OwletDevice.objects.filter(pk=obj.pk).update(name=name)
                results["devices"] += 1

                props = await client.get_properties(dsn)
                props_resp = props.get("response", props)
                vitals = props_resp.get("REAL_TIME_VITALS")
                if not vitals:
                    continue
                # value is usually a JSON string; try to parse if needed
                value = vitals.get("value") if isinstance(vitals, dict) else vitals
                if isinstance(value, str):
                    import json
                    try:
                        value = json.loads(value)
                    except json.JSONDecodeError:
                        value = {}
                if not isinstance(value, dict):
                    continue
                norm = _normalize_vitals(value)

                # Associate reading to the mapped child if present
                child = obj.child
                if not child:
                    continue
                # Upsert reading (ignore duplicates by unique constraint)
                try:
                    with transaction.atomic():
                        OwletReading.objects.create(
                            device=obj,
                            child=child,
                            recorded_at=timezone.now(),
                            measurement_timestamp_epoch=norm.get("measurement_timestamp_epoch"),
                            measurement_timestamp_iso=norm.get("measurement_timestamp_iso"),
                            heart_rate_bpm=norm.get("heart_rate_bpm"),
                            oxygen_saturation_pct=norm.get("oxygen_saturation_pct"),
                            signal_quality=norm.get("signal_quality"),
                            movement_baseline=norm.get("movement_baseline"),
                            movement_value=norm.get("movement_value"),
                            battery_pct=norm.get("battery_pct"),
                            charging=norm.get("charging"),
                            raw_json=value,
                        )
                        results["readings"] += 1
                except Exception:
                    # likely a duplicate due to unique constraint, ignore
                    pass

    # Only consider accounts that have a stored refresh token; otherwise OwletAPI
    # will raise an authentication error (no username/password flow in poller).
    qs = (
        OwletAccount.objects.filter(active=True)
        .exclude(refresh_token_encrypted__isnull=True)
        .exclude(refresh_token_encrypted="")
    )
    for account in qs:
        try:
            await handle_account(account)
        except Exception:
            # Swallow per-account errors to avoid failing the whole poll request.
            # This keeps the endpoint stable even if one account has bad creds
            # or the upstream Owlet API is temporarily unavailable.
            pass
    return results


def poll_all_sync() -> dict[str, Any]:
    """Synchronous poller that isolates Django ORM from async context.

    It runs the Owlet API I/O in a short-lived event loop per account and
    persists results using the ORM in the normal sync context.
    """
    results: dict[str, Any] = {"accounts": 0, "devices": 0, "readings": 0}

    qs = (
        OwletAccount.objects.filter(active=True)
        .exclude(refresh_token_encrypted__isnull=True)
        .exclude(refresh_token_encrypted="")
    )

    for account in qs:

        async def fetch_for_account(a: OwletAccount) -> Tuple[List[dict], List[Tuple[dict, dict, dict]]]:
            items: List[Tuple[dict, dict, dict]] = []
            devices_list: List[dict] = []
            client = OwletClient(a)
            try:
                await client.__aenter__()
                devices = await client.get_devices()
                devices_list = devices or []
                for d in devices_list:
                    dev = d.get("device", d)
                    dsn = dev.get("dsn")
                    name = dev.get("product_name") or dev.get("model") or dsn
                    if not dsn:
                        continue
                    props = await client.get_properties(dsn)
                    props_resp = props.get("response", props)
                    vitals = props_resp.get("REAL_TIME_VITALS")
                    if not vitals:
                        continue
                    value = vitals.get("value") if isinstance(vitals, dict) else vitals
                    if isinstance(value, str):
                        import json
                        try:
                            value = json.loads(value)
                        except json.JSONDecodeError:
                            value = {}
                    if not isinstance(value, dict):
                        continue
                    norm = _normalize_vitals(value)
                    items.append((dev, norm, value))
            finally:
                try:
                    await client.__aexit__(None, None, None)
                except Exception:
                    pass
            return devices_list, items

        try:
            devices_list, fetched_items = asyncio.run(fetch_for_account(account))
        except Exception as e:
            logger.error(f"Error polling Owlet account {account.id}: {e}", exc_info=True)
            continue

        results["accounts"] += 1

        # Ensure devices are persisted even if vitals are not yet available
        for d in devices_list:
            dev = d.get("device", d)
            dsn = dev.get("dsn")
            name = dev.get("product_name") or dev.get("model") or dsn
            if not dsn:
                continue
            obj, _ = OwletDevice.objects.get_or_create(
                account=account,
                dsn=dsn,
                defaults={"name": name or dsn},
            )
            if name and obj.name != name:
                OwletDevice.objects.filter(pk=obj.pk).update(name=name)
            results["devices"] += 1

        # Persist readings only for devices where vitals were retrieved
        for dev, norm, raw in fetched_items:
            dsn = dev.get("dsn")
            name = dev.get("product_name") or dev.get("model") or dsn
            obj, _ = OwletDevice.objects.get_or_create(
                account=account,
                dsn=dsn,
                defaults={"name": name or dsn},
            )

            child = obj.child
            if not child:
                continue

            try:
                with transaction.atomic():
                    OwletReading.objects.create(
                        device=obj,
                        child=child,
                        recorded_at=timezone.now(),
                        measurement_timestamp_epoch=norm.get("measurement_timestamp_epoch"),
                        measurement_timestamp_iso=norm.get("measurement_timestamp_iso"),
                        heart_rate_bpm=norm.get("heart_rate_bpm"),
                        oxygen_saturation_pct=norm.get("oxygen_saturation_pct"),
                        signal_quality=norm.get("signal_quality"),
                        movement_baseline=norm.get("movement_baseline"),
                        movement_value=norm.get("movement_value"),
                        battery_pct=norm.get("battery_pct"),
                        charging=norm.get("charging"),
                        raw_json=raw,
                    )
                    results["readings"] += 1
            except Exception:
                # duplicate unique constraint or other per-row issue; skip
                pass

    return results
