# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Home Assistant custom integration (Python) that registers a
`ConversationEntity` and forwards every Assist query to a configurable
HTTP backend, then returns the backend's `response` to HA's TTS stage.
Integration domain: `http_conversation_agent`. Installed into HA
through HACS as a custom repository (not bind-mounted from disk).

The component is **backend-agnostic** — the `POST {endpoint}` /
`{"text": ...}` → `{"response": ..., "continue_conversation"?: ...}`
contract is the only thing it knows. Anything that speaks that
contract works. See [README.md](README.md) for the contract spec.

## Layout

```
custom_components/http_conversation_agent/
  __init__.py        # setup_entry / unload_entry, registers conversation platform
  config_flow.py     # UI flow: base_url, api_key, endpoint_path, health_path; probes health on save
  conversation.py    # HttpConversationAgent — issues POST, maps reply → ConversationResult
  const.py           # CONF_*, DEFAULT_*, DOMAIN
  manifest.json      # version, deps (conversation), iot_class=local_polling
  strings.json       # i18n for the config flow
hacs.json            # HACS metadata (homeassistant: 2024.1.0 minimum)
```

There is no `tests/` directory and no CI workflows — manual smoke
testing against a real HA install is the verification path.

## Conventions

- **HA 2024.1+ API surface.** `ConversationEntity`, `ConversationInput`,
  `ConversationResult` from `homeassistant.components.conversation`.
  Don't drop to the legacy `async_register` agent API.
- **`aiohttp` via `async_get_clientsession(hass)`** — never make a fresh
  session; reuse HA's shared one.
- **`conversation_id` is logged but not forwarded.** Any session state
  is the backend's job, keyed however it wants.
- **`continue_conversation` round-trip.** When the backend returns
  `true`, set it on the `ConversationResult` so HA's Assist pipeline
  reopens the mic without a new wake-word.
- **Health probe is config-flow-only.** Runtime never re-probes — a
  broken backend just surfaces as a failed Assist turn.
- **Bearer auth header is conditional** on `api_key` being non-empty —
  for unauthenticated backends, no `Authorization` header is sent.

## Versioning & release

Shipping a change to HACS users is a two-step ritual — **a merge to
`main` alone does nothing for existing installs**:

1. Bump `manifest.json::version` (semver) in the same commit as the
   change.
2. Publish a **GitHub Release** with the tag matching that version
   (e.g. `0.3.1`). HACS shows the latest Release to users; without
   one it falls back to commits on the default branch, but users on
   the "show releases only" default never see the update.

There is no build step — the repo's `custom_components/` directory is
what HACS copies into HA verbatim. Don't forget to also call out
breaking contract changes in the release notes (see below).

## Migration history

In 0.3 the integration was renamed from `voice_assistant_bridge` →
`http_conversation_agent` (and "Voice Assistant Bridge" → "HTTP
Conversation Agent") to reflect that it's not voice-assistant-specific.
HA treats the rename as a new integration; users have to remove the old
entry and add the new one. Don't reintroduce the old domain name.

## The `POST /assist` contract

The contract this integration speaks is documented in [README.md](README.md)
and is intentionally backend-agnostic. The integration only knows about
the contract — it makes no assumptions about who implements it.
Changes to the contract are breaking for every backend that has been
configured against this integration, so bump `manifest.json::version`
and call them out in the release notes.
