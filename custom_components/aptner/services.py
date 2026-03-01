from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv

from .const import (
    DOMAIN,
    SERVICE_CANCEL_VISIT_VEHICLE,
    SERVICE_REFRESH,
    SERVICE_REGISTER_VISIT_VEHICLE,
    SERVICE_SUBMIT_SURVEY,
    SERVICE_SUBMIT_VOTE,
)

ATTR_ENTRY_ID = "entry_id"

SERVICE_BASE_SCHEMA = vol.Schema({vol.Optional(ATTR_ENTRY_ID): str})

SERVICE_REFRESH_SCHEMA = SERVICE_BASE_SCHEMA

SERVICE_SUBMIT_VOTE_SCHEMA = SERVICE_BASE_SCHEMA.extend(
    {
        vol.Required("vote_id"): vol.Coerce(int),
        vol.Optional("selection_item_id"): vol.Coerce(int),
        vol.Optional("sign_file_url"): str,
    }
)

SERVICE_SUBMIT_SURVEY_SCHEMA = SERVICE_BASE_SCHEMA.extend(
    {
        vol.Required("survey_id"): vol.Coerce(int),
        vol.Required("answers"): [
            vol.Schema(
                {
                    vol.Required("question_id"): vol.Coerce(int),
                    vol.Required("answer"): str,
                }
            )
        ],
    }
)

SERVICE_REGISTER_VISIT_VEHICLE_SCHEMA = SERVICE_BASE_SCHEMA.extend(
    {
        vol.Required("car_no"): str,
        vol.Required("visitor_phone"): str,
        vol.Required("visit_date"): str,
        vol.Required("visit_purpose"): str,
    }
)

SERVICE_CANCEL_VISIT_VEHICLE_SCHEMA = SERVICE_BASE_SCHEMA.extend(
    {
        vol.Required("visit_reserve_idx"): cv.string,
    }
)


def _get_coordinator(hass: HomeAssistant, entry_id: str | None):
    entries = hass.data.get(DOMAIN, {}).get("entries", {})
    if not entries:
        raise HomeAssistantError("No Aptner entries are configured.")
    if entry_id is not None:
        coordinator = entries.get(entry_id)
        if coordinator is None:
            raise HomeAssistantError(f"Unknown Aptner entry_id: {entry_id}")
        return coordinator
    return next(iter(entries.values()))


async def async_register_services(hass: HomeAssistant) -> None:
    """Register Aptner services."""
    domain_data = hass.data.setdefault(DOMAIN, {})
    if domain_data.get("services_registered"):
        return

    async def handle_refresh(call: ServiceCall) -> None:
        coordinator = _get_coordinator(hass, call.data.get(ATTR_ENTRY_ID))
        await coordinator.async_request_refresh()

    async def handle_submit_vote(call: ServiceCall) -> None:
        coordinator = _get_coordinator(hass, call.data.get(ATTR_ENTRY_ID))
        await coordinator.client.async_submit_vote(
            vote_id=call.data["vote_id"],
            selection_item_id=call.data.get("selection_item_id"),
            sign_file_url=call.data.get("sign_file_url"),
        )
        await coordinator.async_request_refresh()

    async def handle_submit_survey(call: ServiceCall) -> None:
        coordinator = _get_coordinator(hass, call.data.get(ATTR_ENTRY_ID))
        answers = [
            {
                "questionId": answer["question_id"],
                "answer": answer["answer"],
            }
            for answer in call.data["answers"]
        ]
        await coordinator.client.async_submit_survey(
            survey_id=call.data["survey_id"],
            answers=answers,
        )
        await coordinator.async_request_refresh()

    async def handle_register_visit_vehicle(call: ServiceCall) -> None:
        coordinator = _get_coordinator(hass, call.data.get(ATTR_ENTRY_ID))
        await coordinator.client.async_register_visit_vehicle(
            car_no=call.data["car_no"],
            visitor_phone=call.data["visitor_phone"],
            visit_date=call.data["visit_date"],
            visit_purpose=call.data["visit_purpose"],
        )
        await coordinator.async_request_refresh()

    async def handle_cancel_visit_vehicle(call: ServiceCall) -> None:
        coordinator = _get_coordinator(hass, call.data.get(ATTR_ENTRY_ID))
        await coordinator.client.async_cancel_visit_vehicle(
            visit_reserve_idx=call.data["visit_reserve_idx"],
        )
        await coordinator.async_request_refresh()

    hass.services.async_register(
        DOMAIN,
        SERVICE_REFRESH,
        handle_refresh,
        schema=SERVICE_REFRESH_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SUBMIT_VOTE,
        handle_submit_vote,
        schema=SERVICE_SUBMIT_VOTE_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SUBMIT_SURVEY,
        handle_submit_survey,
        schema=SERVICE_SUBMIT_SURVEY_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_REGISTER_VISIT_VEHICLE,
        handle_register_visit_vehicle,
        schema=SERVICE_REGISTER_VISIT_VEHICLE_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_CANCEL_VISIT_VEHICLE,
        handle_cancel_visit_vehicle,
        schema=SERVICE_CANCEL_VISIT_VEHICLE_SCHEMA,
    )
    domain_data["services_registered"] = True


async def async_unregister_services(hass: HomeAssistant) -> None:
    """Unregister Aptner services when the last entry is removed."""
    domain_data = hass.data.get(DOMAIN, {})
    if domain_data.get("entries"):
        return
    if not domain_data.get("services_registered"):
        return

    for service in (
        SERVICE_REFRESH,
        SERVICE_SUBMIT_VOTE,
        SERVICE_SUBMIT_SURVEY,
        SERVICE_REGISTER_VISIT_VEHICLE,
        SERVICE_CANCEL_VISIT_VEHICLE,
    ):
        hass.services.async_remove(DOMAIN, service)
    domain_data["services_registered"] = False
