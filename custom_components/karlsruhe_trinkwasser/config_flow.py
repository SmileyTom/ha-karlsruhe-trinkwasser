"""Config flow for Karlsruhe Trinkwasser."""
from __future__ import annotations

import aiohttp

from homeassistant import config_entries
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PAGE_URL


async def _can_reach_page(hass: HomeAssistant) -> bool:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                PAGE_URL, timeout=aiohttp.ClientTimeout(total=15)
            ) as resp:
                return resp.status == 200
    except Exception:  # noqa: BLE001
        return False


class KarlsruheTrinkwasserConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """One-step config flow – no user input required."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            if not await _can_reach_page(self.hass):
                return self.async_show_form(
                    step_id="user",
                    errors={"base": "cannot_connect"},
                )
            return self.async_create_entry(
                title="Karlsruhe Trinkwasser",
                data={},
            )

        return self.async_show_form(step_id="user")
