"""The Istabai integration."""
from __future__ import annotations

from httpx import TransportError

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_API_KEY,
    CONF_EMAIL,
    CONF_HOST,
    CONF_PASSWORD,
    Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady

from .const import DOMAIN
from .istabai_client import IstabaiClient

# TODO List the platforms that you want to support.
# For your initial PR, limit it to 1 platform.
PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Istabai from a config entry."""

    hass.data.setdefault(DOMAIN, {})

    api = IstabaiClient(entry.data[CONF_HOST])
    try:
        api_key_login = await api.login(api_key=entry.data[CONF_API_KEY])
        if not api_key_login.success:
            user_login = await api.login(
                username=entry.data[CONF_EMAIL], password=entry.data[CONF_PASSWORD]
            )
            if user_login.success:
                entry.data[CONF_API_KEY] = user_login.api_key
            else:
                raise ConfigEntryAuthFailed(
                    "Credentials expired for istabai integration"
                )
    except TransportError as ex:
        raise ConfigEntryNotReady(
            f"Timed out while connecting to {entry.data[CONF_HOST]}"
        ) from ex

    hass.data[DOMAIN][entry.entry_id] = api

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
