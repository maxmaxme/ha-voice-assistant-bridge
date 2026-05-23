# Voice Assistant Bridge

Home Assistant conversation agent that forwards every Assist query to a
self-hosted [`voice-assistant`](https://github.com/maxmaxme/voice-assistant)
HTTP service over `POST /assist` and returns the response to HA's TTS stage.

Designed to slot into the HA Voice PE pipeline:

```
Voice PE ──▶ HA STT ──▶ Voice Assistant Bridge ──POST /assist──▶ voice-assistant ──▶ HA TTS ──▶ Voice PE
```

## Installation (HACS)

One-click via [My Home Assistant](https://my.home-assistant.io/):

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=maxmaxme&repository=ha-voice-assistant-bridge&category=integration)

Or manually:

1. HACS → ⋮ → **Custom repositories** → add
   `https://github.com/maxmaxme/ha-voice-assistant-bridge`, category
   **Integration**.
2. Find **Voice Assistant Bridge** in HACS → Download.
3. Restart Home Assistant.
4. Then add the integration in HA:

   [![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=voice_assistant_bridge)

   Or: Settings → Devices & Services → **Add Integration** → "Voice Assistant Bridge".
5. Fill in:
   - **Base URL** — e.g. `http://localhost:3000` (where your
     voice-assistant service is reachable from the HA container).
   - **API key** — one of the keys from voice-assistant's
     `HTTP_API_KEYS`. Sent as `Authorization: Bearer <key>`.

The config flow probes `/health` before saving, so a typo or unreachable
host surfaces immediately.

## Using as the conversation agent

Settings → Voice assistants → pick your pipeline → **Conversation agent**
→ "Voice Assistant Bridge".

## Contract with the voice-assistant service

- Request: `POST {base_url}/assist` with `{"text": "<user utterance>"}`
- Response: `{"response": "<assistant text>"}`
- Auth: `Authorization: Bearer <api_key>`
- Health probe: `GET {base_url}/health` (used by config_flow only)

This contract is shared with [`maxmaxme/voice-assistant`](https://github.com/maxmaxme/voice-assistant)
and the host stack at [`maxmaxme/home-infra`](https://github.com/maxmaxme/home-infra)
— changes must land in lockstep.

## License

MIT
