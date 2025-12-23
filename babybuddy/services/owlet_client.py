from __future__ import annotations

from typing import Optional, Any
import time

from django.utils import timezone
from asgiref.sync import sync_to_async

from pyowletapi.api import OwletAPI

from owlet.models import OwletAccount, OwletDevice
from babybuddy.services import crypto


class OwletClient:
    """Per-account Owlet API client wrapper that persists refreshed tokens."""

    def __init__(self, account: OwletAccount):
        self.account = account
        token: Optional[str] = None
        expiry: Optional[float] = None
        refresh: Optional[str] = None
        if account.refresh_token_encrypted:
            refresh = crypto.decrypt(account.refresh_token_encrypted)
        self._api = OwletAPI(
            account.region,
            token=token,
            expiry=expiry,
            refresh=refresh,
        )

    async def __aenter__(self) -> "OwletClient":
        await self._api.authenticate()
        await self._persist_tokens_if_changed()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self._api.close()

    async def _persist_tokens_if_changed(self) -> None:
        # OwletAPI exposes headers and internal attributes via tokens property
        tokens = self._api.tokens  # {'api_token', 'expiry', 'refresh'}
        if tokens.get("refresh"):
            enc = crypto.encrypt(tokens["refresh"])
            if enc != self.account.refresh_token_encrypted:
                self.account.refresh_token_encrypted = enc
                self.account.last_auth_at = timezone.now()
                await sync_to_async(self.account.save)(update_fields=[
                    "refresh_token_encrypted",
                    "last_auth_at",
                ])

    async def get_devices(self) -> list[dict[str, Any]]:
        resp = await self._api.get_devices()
        await self._persist_tokens_if_changed()
        devices = resp.get("response", [])
        return devices

    async def get_properties(self, dsn: str) -> dict[str, Any]:
        resp = await self._api.get_properties(dsn)
        await self._persist_tokens_if_changed()
        return resp

