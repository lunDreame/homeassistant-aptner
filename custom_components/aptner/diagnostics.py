from __future__ import annotations

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant

from .const import DOMAIN

REDACT_KEYS = {
    CONF_PASSWORD,
    CONF_USERNAME,
    "accessToken",
    "refreshToken",
    "Authorization",
    "phone",
    "visitor_phone",
    "car_no",
    "address",
    "profileUrl",
    "name",
    "nick",
    "writer",
    "mbId",
    "mbIdx",
    "userIdx",
    "id",
    "tel",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> dict:
    """Return diagnostics for a config entry."""
    coordinator = hass.data[DOMAIN]["entries"][entry.entry_id]
    return async_redact_data(
        {
            "entry": {
                "entry_id": entry.entry_id,
                "title": entry.title,
                "data": dict(entry.data),
                "options": dict(entry.options),
            },
            "coordinator": {
                "last_update_success": coordinator.last_update_success,
                "data": coordinator.data,
            },
        },
        REDACT_KEYS,
    )
