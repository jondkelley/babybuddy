from django.contrib import admin

from .models import OwletAccount, OwletDevice, OwletReading


@admin.register(OwletAccount)
class OwletAccountAdmin(admin.ModelAdmin):
    list_display = ("email", "region", "active", "last_auth_at")
    search_fields = ("email",)
    list_filter = ("region", "active")


@admin.register(OwletDevice)
class OwletDeviceAdmin(admin.ModelAdmin):
    list_display = ("dsn", "name", "account", "child", "active")
    search_fields = ("dsn", "name")
    list_filter = ("active", "account")


@admin.register(OwletReading)
class OwletReadingAdmin(admin.ModelAdmin):
    list_display = (
        "device",
        "child",
        "recorded_at",
        "heart_rate_bpm",
        "oxygen_saturation_pct",
        "signal_quality",
    )
    list_filter = ("device", "child")
    date_hierarchy = "recorded_at"

