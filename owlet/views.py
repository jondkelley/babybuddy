from __future__ import annotations

import asyncio

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import path, reverse

from pyowletapi.api import OwletAPI

from .forms import OwletAccountCreateForm
from core.models import Child
from .models import OwletAccount, OwletDevice
from babybuddy.services import crypto


@login_required
@permission_required("auth.view_user", raise_exception=True)
def settings_list(request):
    accounts = OwletAccount.objects.all().order_by("email")
    return render(request, "owlet/settings_list.html", {"accounts": accounts})


@login_required
@permission_required("auth.change_user", raise_exception=True)
def account_create(request):
    if request.method == "POST":
        form = OwletAccountCreateForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            region = form.cleaned_data["region"]
            password = form.cleaned_data["password"]

            # Exchange for refresh token using OwletAPI
            async def do_auth():
                async with OwletAPI(region, email, password) as api:  # type: ignore[arg-type]
                    # authenticate() will set refresh token via refresh_authentication
                    await api.authenticate()
                    return api.tokens.get("refresh")

            try:
                try:
                    refresh = asyncio.run(do_auth())
                except RuntimeError:
                    refresh = asyncio.get_event_loop().run_until_complete(do_auth())
            except Exception as e:
                messages.error(request, f"Authentication failed: {e}")
                return render(request, "owlet/account_create.html", {"form": form})

            if not refresh:
                messages.error(request, "Could not retrieve refresh token")
                return render(request, "owlet/account_create.html", {"form": form})

            account, _ = OwletAccount.objects.get_or_create(email=email, region=region)
            account.refresh_token_encrypted = crypto.encrypt(refresh)
            account.save()
            messages.success(request, "Owlet account added.")
            return redirect("owlet:settings-list")
    else:
        form = OwletAccountCreateForm()
    return render(request, "owlet/account_create.html", {"form": form})


@login_required
@permission_required("auth.change_user", raise_exception=True)
def device_map(request, account_id: int):
    account = get_object_or_404(OwletAccount, pk=account_id)
    if request.method == "POST":
        device_id = int(request.POST.get("device_id"))
        child_id = request.POST.get("child_id")
        device = get_object_or_404(OwletDevice, pk=device_id, account=account)
        child = None
        if child_id:
            child = get_object_or_404(Child, pk=int(child_id))
        device.child = child
        device.save(update_fields=["child"])
        messages.success(request, "Device mapping updated.")
        return redirect("owlet:device-map", account_id=account.id)

    devices = account.devices.all().order_by("dsn")
    children = Child.objects.all().order_by("last_name", "first_name", "id")
    
    # Fetch latest reading for each device
    from owlet.models import OwletReading
    device_readings = {}
    for device in devices:
        latest_reading = OwletReading.objects.filter(device=device).order_by("-recorded_at").first()
        device_readings[device.id] = latest_reading
    
    return render(
        request,
        "owlet/device_map.html",
        {
            "account": account,
            "devices": devices,
            "children": children,
            "device_readings": device_readings,
        },
    )


app_name = "owlet"

urlpatterns = [
    path("settings/", settings_list, name="settings-list"),
    path("settings/account/create", account_create, name="account-create"),
    path("settings/account/<int:account_id>/devices", device_map, name="device-map"),
]
