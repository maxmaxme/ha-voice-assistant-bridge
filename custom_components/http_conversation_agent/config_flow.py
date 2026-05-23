"""Config flow for the HTTP Conversation Agent integration.

Single-step UI: ask for the backend base URL, an optional Bearer API
key, the conversation endpoint path, and an optional health-probe
path. The flow tries the health path before saving so a typo or
unreachable host surfaces immediately instead of failing at the first
voice command.
"""

from __future__ import annotations

from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_API_KEY,
    CONF_BASE_URL,
    CONF_ENDPOINT_PATH,
    CONF_HEALTH_PATH,
    DEFAULT_BASE_URL,
    DEFAULT_ENDPOINT_PATH,
    DEFAULT_HEALTH_PATH,
    DOMAIN,
)


class HttpConversationAgentConfigFlow(ConfigFlow, domain=DOMAIN):
    """Walk the user through registering an HTTP conversation backend."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Collect endpoint config, then probe health before saving."""
        errors: dict[str, str] = {}
        if user_input is not None:
            base_url = user_input[CONF_BASE_URL].rstrip("/")
            api_key = user_input.get(CONF_API_KEY, "").strip()
            endpoint_path = _normalize_path(
                user_input.get(CONF_ENDPOINT_PATH) or DEFAULT_ENDPOINT_PATH
            )
            health_path = (user_input.get(CONF_HEALTH_PATH) or "").strip()
            if health_path:
                health_path = _normalize_path(health_path)

            await self.async_set_unique_id(f"{base_url}{endpoint_path}")
            self._abort_if_unique_id_configured()

            if health_path:
                session = async_get_clientsession(self.hass)
                try:
                    async with session.get(
                        f"{base_url}{health_path}",
                        timeout=aiohttp.ClientTimeout(total=5),
                    ) as response:
                        if response.status != 200:
                            errors["base"] = "cannot_connect"
                except (aiohttp.ClientError, TimeoutError):
                    errors["base"] = "cannot_connect"

            if not errors:
                return self.async_create_entry(
                    title=f"HTTP Conversation Agent ({base_url}{endpoint_path})",
                    data={
                        CONF_BASE_URL: base_url,
                        CONF_API_KEY: api_key,
                        CONF_ENDPOINT_PATH: endpoint_path,
                        CONF_HEALTH_PATH: health_path,
                    },
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_BASE_URL, default=DEFAULT_BASE_URL): str,
                vol.Optional(CONF_API_KEY, default=""): str,
                vol.Required(
                    CONF_ENDPOINT_PATH, default=DEFAULT_ENDPOINT_PATH
                ): str,
                vol.Optional(
                    CONF_HEALTH_PATH, default=DEFAULT_HEALTH_PATH
                ): str,
            }
        )
        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )


def _normalize_path(path: str) -> str:
    """Ensure a leading slash and no trailing slash."""
    path = path.strip()
    if not path.startswith("/"):
        path = "/" + path
    if len(path) > 1 and path.endswith("/"):
        path = path.rstrip("/")
    return path
