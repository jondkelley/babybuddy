from django.conf import settings
from django.db import models
from django.utils import timezone

from core.models import Child


class OwletAccount(models.Model):
    email = models.EmailField(unique=True)
    region = models.CharField(max_length=16, choices=[("world", "world"), ("europe", "europe")])
    refresh_token_encrypted = models.TextField(blank=True, null=True)
    last_auth_at = models.DateTimeField(blank=True, null=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.email} ({self.region})"


class OwletDevice(models.Model):
    account = models.ForeignKey(OwletAccount, on_delete=models.CASCADE, related_name="devices")
    child = models.ForeignKey(Child, on_delete=models.SET_NULL, related_name="owlet_devices", null=True, blank=True)
    dsn = models.CharField(max_length=64)
    name = models.CharField(max_length=255, blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("account", "dsn")
        indexes = [
            models.Index(fields=["account", "dsn"]),
            models.Index(fields=["child"]),
        ]

    def __str__(self) -> str:
        return f"{self.name or self.dsn}"


class OwletReading(models.Model):
    device = models.ForeignKey(OwletDevice, on_delete=models.CASCADE, related_name="readings")
    child = models.ForeignKey(Child, on_delete=models.CASCADE, related_name="owlet_readings")
    recorded_at = models.DateTimeField(default=timezone.now, db_index=True)
    measurement_timestamp_epoch = models.FloatField(null=True, blank=True, db_index=True)
    measurement_timestamp_iso = models.CharField(max_length=64, null=True, blank=True)

    heart_rate_bpm = models.FloatField(null=True, blank=True)
    oxygen_saturation_pct = models.FloatField(null=True, blank=True)
    signal_quality = models.IntegerField(null=True, blank=True)
    movement_baseline = models.IntegerField(null=True, blank=True)
    movement_value = models.IntegerField(null=True, blank=True)
    battery_pct = models.FloatField(null=True, blank=True)
    charging = models.BooleanField(null=True, blank=True)

    raw_json = models.JSONField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["device", "recorded_at"]),
            models.Index(fields=["child", "recorded_at"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["device", "measurement_timestamp_epoch"],
                name="uniq_device_measurement_ts",
            )
        ]

    def __str__(self) -> str:
        return f"{self.device} @ {self.recorded_at}"

