from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .ble_client import GateBleClient

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = ["button"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    client = GateBleClient(
        hass=hass,
        address=entry.data["address"],
        name=entry.data.get("name"),
    )

    # пробуем подключиться сразу, чтобы видно было в логах "получилось/нет"
    try:
        await client.async_connect()
    except Exception as e:
        _LOGGER.error("Initial BLE connect failed: %s", e)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = client

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    client: GateBleClient = hass.data[DOMAIN].pop(entry.entry_id)
    await client.async_disconnect()
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
