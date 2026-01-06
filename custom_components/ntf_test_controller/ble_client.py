from __future__ import annotations

import asyncio
import logging
from typing import Callable, Optional

from bleak_retry_connector import BleakClientWithServiceCache, establish_connection
from homeassistant.components import bluetooth as ha_bluetooth
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


class GateBleClient:
    """Minimal BLE client for: scan -> connect (Just Works)."""

    def __init__(self, hass: HomeAssistant, address: str, name: str | None = None) -> None:
        self.hass = hass
        self.address = address
        self.name = name or address

        self._client: Optional[BleakClientWithServiceCache] = None
        self._lock = asyncio.Lock()
        self._on_disconnect: Callable[[], None] | None = None

    def set_on_disconnect(self, cb: Callable[[], None]) -> None:
        self._on_disconnect = cb

    @property
    def is_connected(self) -> bool:
        return bool(self._client and self._client.is_connected)

    def _disconnected_cb(self, _client) -> None:
        _LOGGER.warning("BLE disconnected: %s", self.address)
        if self._on_disconnect:
            self._on_disconnect()

    async def async_connect(self) -> None:
        async with self._lock:
            if self._client and self._client.is_connected:
                return

            ble_device = ha_bluetooth.async_ble_device_from_address(
                self.hass,
                self.address,
                connectable=True,
            )
            if ble_device is None:
                raise RuntimeError(f"BLE device not found in HA cache: {self.address}")

            _LOGGER.info("Connecting BLE: %s (%s)", self.name, self.address)

            # IMPORTANT:
            # establish_connection expects a CLASS (callable), not an instance and not HA wrapper
            client = await establish_connection(
                BleakClientWithServiceCache,
                ble_device,
                self.name,
                disconnected_callback=self._disconnected_cb,
                max_attempts=3,
            )

            self._client = client
            _LOGGER.info("Connected BLE: %s (is_connected=%s)", self.address, client.is_connected)

            # Small hold-test to ensure it's not an instant-drop
            await asyncio.sleep(1.5)
            if not client.is_connected:
                raise RuntimeError("BLE connected but dropped within 1.5s")

    async def async_disconnect(self) -> None:
        async with self._lock:
            if not self._client:
                return
            try:
                if self._client.is_connected:
                    await self._client.disconnect()
            finally:
                self._client = None
                _LOGGER.info("Disconnected BLE: %s", self.address)
