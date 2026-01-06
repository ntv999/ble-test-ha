from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components import bluetooth
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN, CONF_ADDRESS, CONF_NAME


def _build_choices(hass) -> dict[str, str]:
    # Берем устройства из кеша HA Bluetooth
    infos = bluetooth.async_discovered_service_info(hass)

    choices: dict[str, str] = {}
    for info in infos:
        addr = getattr(info, "address", None)
        if not addr:
            continue
        name = getattr(info, "name", None) or "Unknown"
        rssi = getattr(info, "rssi", None)
        label = f"{name} ({addr})"
        if rssi is not None:
            label += f" RSSI={rssi}"
        choices[addr] = label

    # Если вообще ничего нет — покажем “заглушку”
    if not choices:
        choices["__none__"] = "No BLE devices in cache yet. Wait 10–20s and press Rescan."
    return dict(sorted(choices.items(), key=lambda x: x[1].lower()))


class NrfGateConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        if user_input is not None:
            if user_input.get("action") == "rescan":
                return await self.async_step_user()

            address = user_input[CONF_ADDRESS]
            if address == "__none__":
                return await self.async_step_user()

            name = user_input.get(CONF_NAME) or address

            await self.async_set_unique_id(address)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=name,
                data={CONF_ADDRESS: address, CONF_NAME: name},
            )

        choices = _build_choices(self.hass)

        schema = vol.Schema(
            {
                vol.Required(CONF_ADDRESS): vol.In(choices),
                vol.Optional(CONF_NAME, default="NRF Gate"): str,
                vol.Optional("action", default=""): vol.In(
                    {"": "Continue", "rescan": "Rescan"}
                ),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema)
