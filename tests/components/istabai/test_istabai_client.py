"Test Istabai client flow"

import logging
import string
import httpx
import pytest

from homeassistant.components.istabai.istabai_client import IstabaiClient
from homeassistant.components.istabai.istabai_client import *
from homeassistant.core import HomeAssistant
from unittest.mock import patch
from typing import Type


class TestData:
    """Tes payloads from the API"""

    @staticmethod
    def get_login_json() -> any:
        """Returns the json response expected for succesful login"""

        return {
            "home_invitations": [],
            "homes": TestData.get_part_homes_json(),
            "timestamp": 1678044952,
            "user": TestData.get_part_user_json(),
        }

    @staticmethod
    def get_json_error(code: int, description: string) -> any:
        """Returns the payload for errors with the specified code and description"""

        return {"error": {"code": code, "description": description}}

    @staticmethod
    def get_invalid_login_json() -> any:
        """Returns the json response expected for an invalid login"""

        return TestData.get_json_error(401, "Invalid email or password.")

    @staticmethod
    def get_part_home_invitations_json() -> any:
        """Gets a payload part of home invitations, which is part of multiple replies.
        Since this is currently unused, we leave it empty"""
        return []

    @staticmethod
    def get_part_homes_json() -> any:
        """Gets a payload part of home, which is part of multiple replies."""

        # TODO remove personal details...
        return [
            {
                "address": None,
                "boiler": False,
                "boiler_delay": True,
                "boiler_delay_timeout": "5",
                "features": [],
                "has_boiler": True,
                "id": 5,
                "last_motion": 1678043608,
                "location": None,
                "mode": "123",
                "name": "Persepolis",
                "notifications": 117,
                "offline_mode": True,
                "owner_user_id": 10,
                "rooms": 4,
                "schedules": [
                    {"default": True, "id": 101, "name": "Schedule 1"},
                    {"default": False, "id": 102, "name": "Schedule 2"},
                    {"default": False, "id": 103, "name": "Schedule 3"},
                    {"default": False, "id": 104, "name": "Schedule 4"},
                ],
                "time_zone": "Europe/Bucharest",
                "warnings": 0,
            }
        ]

    @staticmethod
    def get_part_user_json() -> any:
        """Returns a user description, which is returned on login. This is just important enough to have it's own method"""
        return {
            "api_key": TestData.get_data_api_key(),
            "homes": 1,
            "id": 10,
            "lang": "EN",
            "name": "Fluffy Bread",
        }

    @staticmethod
    def get_data_test_api_key() -> str:
        """Mock api key for the tests"""
        # TODO merge in the main redirection method
        return "api_test_key"

    # TODO remove
    @staticmethod
    def get_data_real_api_key() -> str:
        """Real API KEY needs to be removed"""
        return ""

    @staticmethod
    def get_data_api_key() -> str:
        """Redirection for the api key"""
        return TestData.get_data_real_api_key()


async def test_login_success() -> None:
    "Test for when the login succeds"

    with patch("httpx.AsyncClient.get") as get_mock:

        def get_side_effect(url, **kwargs):
            request = httpx.Request("GET", url, **kwargs)
            return httpx.Response(200, json=TestData.get_login_json(), request=request)

        get_mock.side_effect = get_side_effect

        client = IstabaiClient("some@email.com", "some-password")
        login_result = await client.login()

        assert login_result is True
        assert client.api_key == TestData.get_data_api_key()


async def test_login_fail_with_invalid_login() -> None:
    "Test for when the wrong login credentials are provided"

    with patch("httpx.AsyncClient.get") as get_mock:

        def get_side_effect(url, **kwargs):
            request = httpx.Request("GET", url, **kwargs)
            return httpx.Response(
                200, json=TestData.get_invalid_login_json(), request=request
            )

        get_mock.side_effect = get_side_effect

        client = IstabaiClient("wrong@email.com", "some-wrong-password")
        login_result = await client.login()

        assert login_result is False
        assert client.api_key is None


@pytest.mark.parametrize(
    "status_code, expected_exception",
    [
        (300, IstabaiInvalidApiKey),
        (100, IstabaiUnavailble),
        (203, IstabaiInvalidRequest),
        (500, IstabaiUnexpectedStatusCode),
        (404, IstabaiUnexpectedStatusCode),
        (401, IstabaiUnexpectedStatusCode),
        (403, IstabaiUnexpectedStatusCode),
        (400, IstabaiUnexpectedStatusCode),
    ],
)
async def test_login_whith_error_status_code(
    status_code: int, expected_exception: type[BaseException]
) -> None:
    """Validates the behavior of the API when reciving non-200 HTTP status codes."""

    with patch("httpx.AsyncClient.get") as get_mock:

        def get_side_effect(url, **kwargs):
            request = httpx.Request("GET", url, **kwargs)
            return httpx.Response(status_code, request=request)

        get_mock.side_effect = get_side_effect

        client = IstabaiClient("abc", "")
        with pytest.raises(expected_exception) as api_exception_info:
            await client.login()

        # TODO check properties of the errors


async def test_login_with_json_error_payload(
    code: int, description: string, expected_exception: type[BaseException]
) -> None:
    """To implement later"""

    assert False is True


@pytest.mark.skip(reason="let's see the failure first")
async def test_login_other_response_non_json() -> None:
    """To implement later"""

    assert False is True
