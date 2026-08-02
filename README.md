# Reciplease for Home Assistant

A Home Assistant custom integration that surfaces basic info from your [Reciplease](https://github.com/reciplease/reciplease)
house: inventory counts and upcoming planned meals.

This repo has two parts:

- `src/reciplease_hass/` — a standalone async client library for the Reciplease API. No Home
  Assistant imports; the integration is a thin wrapper around it.
- `custom_components/reciplease/` — the actual Home Assistant integration (config flow,
  coordinator, sensors).

## Requirements

- A Reciplease house you own (or are a member of), with the backend deployed somewhere
  reachable from your Home Assistant instance.
- A house **API key**: from the Reciplease web app, go to **House settings → API keys** and
  create one (owners only). Give it a name (e.g. "Home Assistant") and pick a role — `Read only`
  is enough for this integration, since it only reads data.

## Installation

### HACS (custom repository)

1. In HACS, go to **Integrations → ⋮ → Custom repositories**.
2. Add `https://github.com/reciplease/reciplease-hass`, category **Integration**.
3. Install "Reciplease", then restart Home Assistant.

### Manual

1. Copy `custom_components/reciplease` into your Home Assistant `config/custom_components/`
   directory.
2. Restart Home Assistant.

## Setup

1. In Home Assistant, go to **Settings → Devices & services → Add integration**, search for
   "Reciplease".
2. Enter your Reciplease deployment's base URL (e.g. `https://api.example.com`) and the API key
   you created above.

This creates one device per house, with sensors for:

- Inventory items
- Expired inventory items
- Upcoming planned meals (next 14 days)
- Next planned meal

## Development

```sh
python3 -m venv .venv
.venv/bin/pip install -e ".[test]"
.venv/bin/pip install homeassistant  # needed for the custom_components tests
.venv/bin/python -m pytest
```

The library (`src/reciplease_hass/`) and the integration (`custom_components/reciplease/`) are
tested independently — `tests/test_client.py` for the former,
`tests/custom_components/reciplease/` for the latter.

## License

GPL-3.0-or-later, matching [reciplease/reciplease](https://github.com/reciplease/reciplease).
