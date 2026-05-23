"""Conversation entity that forwards user text to an HTTP backend."""

from __future__ import annotations

import asyncio
import logging
from typing import Literal

import aiohttp
from homeassistant.components import conversation
from homeassistant.components.conversation import (
    ConversationEntity,
    ConversationInput,
    ConversationResult,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import intent
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_API_KEY,
    CONF_BASE_URL,
    CONF_ENDPOINT_PATH,
    DEFAULT_ENDPOINT_PATH,
    DEFAULT_TIMEOUT_SEC,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Register the conversation entity for this config entry."""
    async_add_entities([HttpConversationAgent(entry)])


class HttpConversationAgent(ConversationEntity):
    """HA conversation agent that delegates to a generic HTTP backend.

    The backend must implement the minimal contract:

        POST {base_url}{endpoint_path}
            Content-Type: application/json
            Authorization: Bearer <api_key>   (optional)
            Body: {"text": "<user utterance>"}
            Reply: {"response": "<assistant text>",
                    "continue_conversation"?: bool}

    Session state, if any, is the backend's responsibility — HA's
    `conversation_id` is logged but not forwarded.
    """

    _attr_has_entity_name = True
    _attr_name = "HTTP Conversation Agent"
    _attr_supported_features = conversation.ConversationEntityFeature(0)

    def __init__(self, entry: ConfigEntry) -> None:
        """Store the config entry; URL/key are read fresh on each call."""
        self._entry = entry
        self._attr_unique_id = entry.entry_id

    @property
    def supported_languages(self) -> list[str] | Literal["*"]:
        """Language handling is the backend's responsibility."""
        return conversation.MATCH_ALL

    async def async_process(self, user_input: ConversationInput) -> ConversationResult:
        """Forward `user_input.text` to the configured HTTP endpoint."""
        base_url = self._entry.data[CONF_BASE_URL].rstrip("/")
        api_key = (self._entry.data.get(CONF_API_KEY) or "").strip()
        endpoint_path = self._entry.data.get(
            CONF_ENDPOINT_PATH, DEFAULT_ENDPOINT_PATH
        )
        url = f"{base_url}{endpoint_path}"
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        body = {"text": user_input.text}

        _LOGGER.debug(
            "Forwarding to HTTP backend url=%s text=%r conv_id=%s",
            url,
            user_input.text,
            user_input.conversation_id,
        )

        session = async_get_clientsession(self.hass)
        try:
            async with session.post(
                url,
                json=body,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT_SEC),
            ) as response:
                response.raise_for_status()
                data = await response.json()
        except asyncio.TimeoutError:
            return _error_result(
                user_input,
                f"HTTP backend timed out (>{DEFAULT_TIMEOUT_SEC}s)",
            )
        except aiohttp.ClientResponseError as err:
            return _error_result(
                user_input,
                f"HTTP backend returned {err.status}: {err.message}",
            )
        except Exception as err:  # noqa: BLE001
            _LOGGER.exception("HTTP backend request failed")
            return _error_result(user_input, f"HTTP backend unreachable: {err}")

        reply_text = (data or {}).get("response", "")
        if not reply_text:
            _LOGGER.warning("HTTP backend returned empty reply: %r", data)
            return _error_result(user_input, "HTTP backend returned empty reply")

        response_intent = intent.IntentResponse(language=user_input.language)
        response_intent.async_set_speech(reply_text)
        return ConversationResult(
            response=response_intent,
            conversation_id=user_input.conversation_id,
            continue_conversation=bool((data or {}).get("continue_conversation")),
        )


def _error_result(user_input: ConversationInput, message: str) -> ConversationResult:
    """Build a ConversationResult carrying an error response."""
    response_intent = intent.IntentResponse(language=user_input.language)
    response_intent.async_set_error(
        intent.IntentResponseErrorCode.UNKNOWN,
        message,
    )
    return ConversationResult(
        response=response_intent,
        conversation_id=user_input.conversation_id,
    )
