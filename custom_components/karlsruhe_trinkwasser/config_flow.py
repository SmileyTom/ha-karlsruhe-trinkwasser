"""Config flow for Karlsruhe Trinkwasser."""
from __future__ import annotations

import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers import selector

from .const import (
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    PAGE_URL,
    SCAN_INTERVAL_OPTIONS,
)


async def _can_reach_page(hass: HomeAssistant) -> bool:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                PAGE_URL, timeout=aiohttp.ClientTimeout(total=15)
            ) as resp:
                return resp.status == 200
    except Exception:  # noqa: BLE001
        return False


def _interval_schema(current: int) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_SCAN_INTERVAL, default=str(current)): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[
                        selector.SelectOptionDict(value=v, label=l)
                        for v, l in SCAN_INTERVAL_OPTIONS
                    ],
                    mode=selector.SelectSelectorMode.LIST,
                )
            )
        }
    )


class KarlsruheTrinkwasserConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow – one step, interval selection."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            if not await _can_reach_page(self.hass):
                return self.async_show_form(
                    step_id="user",
                    data_schema=_interval_schema(DEFAULT_SCAN_INTERVAL),
                    errors={"base": "cannot_connect"},
                )
            return self.async_create_entry(
                title="Karlsruhe Trinkwasser",
                data={},
                options={CONF_SCAN_INTERVAL: int(user_input[CONF_SCAN_INTERVAL])},
            )

        return self.async_show_form(
            step_id="user",
            data_schema=_interval_schema(DEFAULT_SCAN_INTERVAL),
        )

    @staticmethod
    @config_entries.callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> KarlsruheTrinkwasserOptionsFlow:
        return KarlsruheTrinkwasserOptionsFlow()


class KarlsruheTrinkwasserOptionsFlow(config_entries.OptionsFlow):
    """Options flow – change the poll interval."""

    async def async_step_init(self, user_input=None):
        current = self.config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        if user_input is not None:
            return self.async_create_entry(
                data={CONF_SCAN_INTERVAL: int(user_input[CONF_SCAN_INTERVAL])},
            )
        return self.async_show_form(
            step_id="init",
            data_schema=_interval_schema(current),
        )
