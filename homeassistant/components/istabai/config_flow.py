"""Config flow for Istabai integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY, CONF_EMAIL, CONF_HOST, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import selector

from .const import CONF_SELECTED_HOME_LIST, DOMAIN
from .istabai_client import IstabaiClient

_LOGGER = logging.getLogger(__name__)

STEP_USER = "user"
STEP_HOME = "home_selection"
STEP_ROOM = "room"
STEPS = [STEP_USER, STEP_ROOM]

# TODO move some to const?
CONF_AVAILABLE_HOME_LIST = "available_home_list"
CONF_AVAILABLE_ROOM_LIST_PREFIX = "available_room_list_home_id_"
CONF_SELECTED_ROOM_LIST_PREFIX = "selected_room_list_home_id_"

# TODO adjust the data schema to the data that you need
STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST, default="https://api.istabai.com"): str,
        vol.Required(CONF_EMAIL): str,
        vol.Required(CONF_PASSWORD): str,
    }
)

STEP_HOME_DATA_SCHEMA = vol.Schema({vol.Required("home_id"): str})

STEP_ROOM_DATA_SCHEMA = vol.Schema({vol.Required("room_id"): str})


async def validate_input_user(
    hass: HomeAssistant, data: dict[str, Any]
) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    # TODO validate the data can be used to set up a connection.

    # If your PyPI package is not built with async, pass your methods
    # to the executor:
    # await hass.async_add_executor_job(
    #     your_validate_func, data["username"], data["password"]
    # )

    client = IstabaiClient(data[CONF_HOST])
    auth_response = await client.login(data[CONF_EMAIL], data[CONF_PASSWORD])
    if not auth_response.success:
        raise InvalidAuth
    available_home_list: dict[int, str] = {}
    for home_dto in auth_response.full_response.homes:
        available_home_list[home_dto.id] = home_dto.name
    return {
        CONF_HOST: data[CONF_HOST],
        CONF_EMAIL: data[CONF_EMAIL],
        CONF_PASSWORD: data[CONF_PASSWORD],
        CONF_API_KEY: auth_response.api_key,
        CONF_AVAILABLE_HOME_LIST: available_home_list,
    }


async def validate_input_home(
    hass: HomeAssistant, user_data: dict[str, Any], homes_input: dict[str, Any]
) -> dict[str, Any]:
    client = IstabaiClient(user_data[CONF_HOST])
    auth_response = await client.login(api_key=user_data[CONF_API_KEY])
    home_list: list[int] = homes_input[CONF_SELECTED_HOME_LIST]
    home_result: dict[str, any] = {CONF_SELECTED_HOME_LIST: home_list}
    for home_id in home_list:
        found: bool = False
        for server_home in auth_response.full_response.homes:
            if server_home.id == int(home_id):
                found = True
                break
        if not found:
            raise InvalidHomeSelection

        room_response = await client.get_rooms(home_id)
        available_rooms: dict[int, str] = {}
        for room in room_response.rooms:
            available_rooms[room.id] = room.name
        home_result[f"{CONF_AVAILABLE_ROOM_LIST_PREFIX}{home_id}"] = available_rooms

    return home_result


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Istabai."""

    VERSION = 1

    data_step_user = dict[str, Any]
    data_step_home = dict[str, Any]

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id=STEP_USER, data_schema=STEP_USER_DATA_SCHEMA
            )

        errors: dict[str, str] = {}
        try:
            info = await validate_input_user(self.hass, user_input)
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except InvalidAuth:
            errors["base"] = "invalid_auth"
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            self.data_step_user = info
            return await self.async_step_home_selection()

        return self.async_show_form(
            step_id=STEP_USER, data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_home_selection(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        home_value_list = [
            selector.SelectOptionDict(value=str(home_id), label=home_name)
            for (home_id, home_name) in self.data_step_user[
                CONF_AVAILABLE_HOME_LIST
            ].items()
        ]
        dyn_schema = vol.Schema(
            {
                vol.Required(
                    CONF_SELECTED_HOME_LIST, default=[]
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=home_value_list, multiple=True
                    )
                )
            }
        )
        if user_input is None:
            return self.async_show_form(step_id=STEP_HOME, data_schema=dyn_schema)

        errors: dict[str, str] = {}

        try:
            info = await validate_input_home(self.hass, self.data_step_user, user_input)
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except InvalidAuth:
            errors["base"] = "invalid_auth"
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            self.data_step_home = info
            return await self.async_step_room_selection()

        return self.async_show_form(
            step_id=STEP_HOME, data_schema=dyn_schema, errors=errors
        )

    async def async_step_room_selection(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        # TODO we may probably want to be able to setup which rooms to integrate and which not?
        # TODO figure out what the title should be?
        return await self.aggregate_data_and_create_entry()

        # schema_obj = {
        #     # vol.Optional(CONF_SELECTED_HOME_LIST + "_x", default=[]): vol.All(
        #     #     cv.ensure_list, [vol.In(self.data_step_user[CONF_AVAILABLE_HOME_LIST])]),
        #     vol.Required("test"): vol.basestring
        # }

        # for home in self.data_step_home[CONF_SELECTED_HOME_LIST]:
        #     for available_room in self.data_step_home[f"{CONF_AVAILABLE_ROOM_LIST_PREFIX}{home}"]:
        #         schema_obj[vol.Required(f"room_{available_room}")] = vol.Boolean(True)
        #
        # dyn_schema = vol.Schema(schema_obj)
        # if user_input is None:
        #     return self.async_show_form(step_id=STEP_ROOM, data_schema=dyn_schema)
        #
        # errors: dict[str, str] = {}
        # try:
        #     info = await validate_input_home(self.hass, self.data_step_user, user_input)
        # except CannotConnect:
        #     errors["base"] = "cannot_connect"
        # except InvalidAuth:
        #     errors["base"] = "invalid_auth"
        # except Exception:  # pylint: disable=broad-except
        #     _LOGGER.exception("Unexpected exception")
        #     errors["base"] = "unknown"
        # else:
        #     raise NotImplementedError("not implemented", info)
        #
        # return self.async_show_form(step_id=STEP_ROOM, data_schema=dyn_schema, errors=errors)

    async def aggregate_data_and_create_entry(self) -> FlowResult:
        final_data = {
            CONF_HOST: self.data_step_user[CONF_HOST],
            CONF_EMAIL: self.data_step_user[CONF_EMAIL],
            CONF_PASSWORD: self.data_step_user[CONF_PASSWORD],
            CONF_API_KEY: self.data_step_user[CONF_API_KEY],
            CONF_SELECTED_HOME_LIST: self.data_step_home[CONF_SELECTED_HOME_LIST],
        }
        return self.async_create_entry(title="Istabai Sensors Test", data=final_data)


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""


class InvalidHomeSelection(HomeAssistantError):
    """Error to indicate the user somehow selected a home not in his available home list"""
