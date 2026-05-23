"""The HTTP Conversation Agent integration.

Routes HA Assist conversation requests to any HTTP backend that speaks
the minimal contract:

    POST {base_url}{endpoint_path}
        Content-Type: application/json
        Authorization: Bearer <api_key>   (optional)
        Body: {"text": "<user utterance>"}
        Reply: {"response": "<assistant text>",
                "continue_conversation"?: bool}

STT and TTS slots in HA's pipeline are not affected — they keep using
whatever the user has configured (Whisper / Piper / OpenAI / etc.).
"""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

PLATFORMS = [Platform.CONVERSATION]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up HTTP Conversation Agent from a config entry."""
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a HTTP Conversation Agent config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
