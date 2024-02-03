"""Config flow for Istabai integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN
from .istabai_client import IstabaiClient

_LOGGER = logging.getLogger(__name__)

STEP_USER = "user"
STEP_ROOM = "room_selection"
STEPS = ["user", "room_selection"]

# TODO adjust the data schema to the data that you need
STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("host", default="https://api.istabai.com"): str,
        vol.Required("username"): str,
        vol.Required("password"): str,
    }
)

STEP_ROOM_DATA_SCHEMA = vol.Schema({vol.Required("home_id"): str})


class PlaceholderHub:
    """Placeholder class to make tests pass.

    TODO Remove this placeholder class and replace with things from your PyPI package.
    """

    def __init__(self, host: str) -> None:
        """Initialize."""
        self.host = host

    async def authenticate(self, username: str, password: str) -> bool:
        """Test if we can authenticate with the host."""
        return True


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    # TODO validate the data can be used to set up a connection.

    # If your PyPI package is not built with async, pass your methods
    # to the executor:
    # await hass.async_add_executor_job(
    #     your_validate_func, data["username"], data["password"]
    # )
    raise InvalidAuth
    # client = IstabaiClient(data["username"], data["password"], data["host"])
    # Placeholderclient(data["host"])

    # if not await client.login():
    #     raise InvalidAuth

    # If you cannot connect:
    # throw CannotConnect
    # If the authentication is wrong:
    # InvalidAuth

    # Return info that you want to store in the config entry.
    # return {"title": "Name of the device"}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Istabai."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id=STEP_USER, data_schema=STEP_USER_DATA_SCHEMA
            )

        if self.cur_step["step_id"] == STEP_USER:
            errors = {}

            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_show_form(
                    step_id=STEP_ROOM, data_schema=STEP_ROOM_DATA_SCHEMA, errors=errors
                )

            return self.async_show_form(
                step_id=STEP_USER, data_schema=STEP_USER_DATA_SCHEMA, errors=errors
            )

        if self.cur_step["step_id"] == STEP_ROOM:
            errors["base"] = "not_implemented"

            return self.async_show_form(
                step_id=STEP_ROOM, data_schema=STEP_ROOM_DATA_SCHEMA, errors=errors
            )

            # return self.async_create_entry(title=info["title"], data=user_input)


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
