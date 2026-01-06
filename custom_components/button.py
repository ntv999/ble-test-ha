from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .ble_client import GateBleClient


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    client: GateBleClient = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([ReconnectButton(client), DisconnectButton(client)])


class _Base(ButtonEntity):
    _attr_has_entity_name = True

    def __init__(self, client: GateBleClient) -> None:
        self.client = client

    @property
    def available(self) -> bool:
        return True


class ReconnectButton(_Base):
    _attr_name = "Reconnect"
    _attr_icon = "mdi:bluetooth-connect"

    async def async_press(self) -> None:
        await self.client.async_disconnect()
        await self.client.async_connect()


class DisconnectButton(_Base):
    _attr_name = "Disconnect"
    _attr_icon = "mdi:bluetooth-off"

    async def async_press(self) -> None:
        await self.client.async_disconnect()
