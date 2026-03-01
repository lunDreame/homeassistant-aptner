from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import AptnerApiClient, AptnerApiError
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class AptnerDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinate Aptner API polling."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: AptnerApiClient,
        *,
        update_interval: timedelta = DEFAULT_SCAN_INTERVAL,
    ) -> None:
        super().__init__(
            hass,
            logger=hass.data.get(DOMAIN, {}).get("logger", _LOGGER),
            name=DOMAIN,
            update_interval=update_interval,
        )
        self.client = client

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            return await self.client.async_fetch_dashboard()
        except (AptnerApiError, aiohttp.ClientError, OSError) as err:
            raise UpdateFailed(str(err)) from err
