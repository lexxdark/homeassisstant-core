"""Test Istabai client flow"""

import string
from unittest.mock import patch

import httpx
import pytest

from homeassistant.components.istabai.istabai_client import *


class TestData:
    """Tes payloads from the API"""

    @staticmethod
    def get_login_json() -> any:
        """Returns the json response expected for successful login"""

        return {
            "home_invitations": [],
            "homes": TestData.get_part_homes_json(),
            "timestamp": 1678044952,
            "user": TestData.get_part_user_json(),
        }

    @staticmethod
    def get_homes_response_json() -> any:
        """Returns the json response expected for a successful get homes call"""

        return {
            "timestamp": 1707516670,
            "homes": TestData.get_part_homes_json(),
            # home_invitations left to implement later
        }

    @staticmethod
    def get_rooms_response_json() -> any:
        """Returns the json response expected for a successful get room call"""

        return {
            "timestamp": 1707701355,
            "rooms": TestData.get_part_rooms_json(),
            "home": TestData.get_part_home_json(),
            "home_count": 1,
        }

    @staticmethod
    def set_temperature_response_json() -> any:
        """Returns the json response for successful set temperature call"""

        return {"set_temperature": {"room_id": 204, "mode": "ECO", "temperature": 17.2}}

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
        Since this is currently unused, we leave it empty
        """
        return []

    @staticmethod
    def get_part_home_json() -> any:
        """Gets a home for test data"""
        return {
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
            "name": "The Crumb Matrix",
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

    @staticmethod
    def get_part_homes_json() -> any:
        """Gets a payload part of home, which is part of multiple replies."""

        # TODO remove personal details...
        return [TestData.get_part_home_json()]

    @staticmethod
    def get_part_rooms_json() -> any:
        return [
            {
                "id": 201,
                "read_only": False,
                "name": "Living",
                "temperature": 24,
                "min_temperature": 10,
                "max_temperature": 25,
                "motion_sensor_armed": True,
                "set_temperature": {
                    "day": 23,
                    "night": 23,
                    "eco": 15,
                    "temp": 19,
                    "offline": 23,
                    "boost": False,
                },
                "humidity": 59,
                "device": {
                    "faulty": False,
                    "battery": 0.91,
                    "charging": False,
                    "signal": 0.54,
                    "last_data": 1707701247,
                },
                "last_motion": 1707701274,
                "has_motion_sensor": True,
                "is_water": False,
                "on_schedule": True,
                "boost_until": False,
                "boost_until_normal": False,
                "mode": "ECO",
                "active_schedule_id": 7512,
            },
            {
                "id": 202,
                "read_only": False,
                "name": "Dormitor",
                "temperature": 24,
                "min_temperature": 15,
                "max_temperature": 30,
                "motion_sensor_armed": True,
                "set_temperature": {
                    "day": 22,
                    "night": 24,
                    "eco": 15,
                    "temp": 23,
                    "offline": 23,
                    "boost": False,
                },
                "humidity": 60,
                "device": {
                    "faulty": False,
                    "battery": 0.92,
                    "charging": False,
                    "signal": 0.99,
                    "last_data": 1707701155,
                },
                "last_motion": None,
                "has_motion_sensor": False,
                "is_water": False,
                "on_schedule": True,
                "boost_until": False,
                "boost_until_normal": False,
                "mode": "NIGHT",
                "active_schedule_id": 11697,
            },
            {
                "id": 203,
                "read_only": False,
                "name": "Camera fete",
                "temperature": 23.6,
                "min_temperature": 15,
                "max_temperature": 30,
                "motion_sensor_armed": True,
                "set_temperature": {
                    "day": 23.5,
                    "night": 23,
                    "eco": 15,
                    "temp": 24.5,
                    "offline": 23,
                    "boost": False,
                },
                "humidity": 54,
                "device": {
                    "faulty": False,
                    "battery": 0.27,
                    "charging": False,
                    "signal": 0.86,
                    "last_data": 1707701131,
                },
                "last_motion": None,
                "has_motion_sensor": False,
                "is_water": False,
                "on_schedule": True,
                "boost_until": False,
                "boost_until_normal": False,
                "mode": "NIGHT",
                "active_schedule_id": 11492,
            },
            {
                "id": 204,
                "read_only": False,
                "name": "Birou",
                "temperature": 23.7,
                "min_temperature": 5,
                "max_temperature": 30,
                "motion_sensor_armed": True,
                "set_temperature": {
                    "day": 23.5,
                    "night": 23.5,
                    "eco": 15,
                    "temp": 23.5,
                    "offline": 23.1,
                    "boost": 20.5,
                },
                "humidity": 48,
                "device": {
                    "faulty": False,
                    "battery": 0.92,
                    "charging": False,
                    "signal": 0.61,
                    "last_data": 1707701257,
                },
                "last_motion": None,
                "has_motion_sensor": False,
                "is_water": False,
                "on_schedule": True,
                "boost_until": 1707712076,
                "boost_until_normal": 1707704876,
                "mode": "BOOST",
                "active_schedule_id": 7512,
            },
        ]

    @staticmethod
    def get_part_user_json() -> any:
        """Returns a user description, which is returned on login.
        This is just important enough to have its own method
        """
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
        return "some-secrete-api-key"

    @staticmethod
    def get_data_api_key() -> str:
        """Redirection for the api key"""
        return TestData.get_data_real_api_key()


@pytest.mark.parametrize(
    "expected_message, username, password, api_key",
    [
        ("You must send either the credentials or the api key", None, None, None),
        ("Either send api_key or credentials not both", "user", "password", "key"),
        ("Either send api_key or credentials not both", "user", None, "key"),
        ("Either send api_key or credentials not both", None, "password", "key"),
        (
            "When sending the credentials you must provide both the username and password",
            None,
            "password",
            None,
        ),
        (
            "When sending the credentials you must provide both the username and password",
            "user",
            None,
            None,
        ),
    ],
)
async def test_login_input_validation_no_input(
    username: Optional[str],
    password: Optional[str],
    api_key: Optional[str],
    expected_message: str,
) -> None:
    client = IstabaiClient()

    with pytest.raises(IstabaiInvalidApiUsage) as api_exception_info:
        await client.login(username, password, api_key)

    assert api_exception_info.value.message == expected_message


async def test_login_success() -> None:
    """Test for when the login succeeds"""

    with patch("httpx.AsyncClient.get") as get_mock:

        def get_side_effect(url, **kwargs):
            request = httpx.Request("GET", url, **kwargs)
            return httpx.Response(200, json=TestData.get_login_json(), request=request)

        get_mock.side_effect = get_side_effect

        client = IstabaiClient()
        login_result = await client.login("some@email.com", "some-password")

        assert login_result is not None
        assert login_result.success is True
        assert login_result.api_key is not None
        assert login_result.api_key == TestData.get_data_api_key()
        assert client._api_key == TestData.get_data_api_key()


async def test_login_fail_with_invalid_login() -> None:
    """Test for when the wrong login credentials are provided"""

    with patch("httpx.AsyncClient.get") as get_mock:

        def get_side_effect(url, **kwargs):
            request = httpx.Request("GET", url, **kwargs)
            return httpx.Response(
                200, json=TestData.get_invalid_login_json(), request=request
            )

        get_mock.side_effect = get_side_effect

        client = IstabaiClient()
        login_result = await client.login("wrong@email.com", "some-wrong-password")

        assert login_result is not None
        assert login_result.success is False
        assert login_result.api_key is None
        assert login_result.full_response is None
        assert client._api_key is None


@pytest.mark.parametrize(
    "status_code, expected_exception",
    [
        (300, IstabaiInvalidApiKey),
        (100, IstabaiUnavailable),
        (203, IstabaiInvalidRequest),
        (500, IstabaiUnexpectedStatusCode),
        (404, IstabaiUnexpectedStatusCode),
        (401, IstabaiUnexpectedStatusCode),
        (403, IstabaiUnexpectedStatusCode),
        (400, IstabaiUnexpectedStatusCode),
    ],
)
async def test_login_with_error_status_code(
    status_code: int, expected_exception: type[BaseException]
) -> None:
    """Validates the behavior of the API when receiving  non-200 HTTP status codes."""

    with patch("httpx.AsyncClient.get") as get_mock:

        def get_side_effect(url, **kwargs):
            request = httpx.Request("GET", url, **kwargs)
            return httpx.Response(status_code, request=request)

        get_mock.side_effect = get_side_effect

        client = IstabaiClient()
        with pytest.raises(expected_exception) as api_exception_info:
            await client.login("abc", "")

        if api_exception_info.type is IstabaiUnexpectedStatusCode:
            assert api_exception_info.value.code == status_code
        # TODO check properties of the errors


async def test_login_other_response_non_json() -> None:
    """When the server for whatever reason does not return a jons"""

    with patch("httpx.AsyncClient.get") as get_mock:

        def get_side_effect(url, **kwargs):
            request = httpx.Request("GET", url, **kwargs)
            content = "Some error returned in plain text"
            headers = {"Content-Type": "text/plain"}
            return httpx.Response(
                200, request=request, content=content, headers=headers
            )

        get_mock.side_effect = get_side_effect

        client = IstabaiClient()
        with pytest.raises(IstabaiUnexpectedResponse) as api_exception_info:
            await client.login("wrong@email.com", "some-wrong-password")

        # TODO test properties of response


@pytest.mark.parametrize(
    "code, message, expected_exception",
    [
        (300, "some exception", IstabaiGenericError),
        (500, "some kind of server crash maybe", IstabaiGenericError),
    ],
)
async def test_login_with_json_error_payload(
    code: int, message: string, expected_exception: type[BaseException]
) -> None:
    """To implement later"""
    # TODO fix description?
    with patch("httpx.AsyncClient.get") as get_mock:

        def get_side_effect(url, **kwargs):
            request = httpx.Request("GET", url, **kwargs)
            content = TestData.get_json_error(code, message)
            return httpx.Response(200, request=request, json=content)

        get_mock.side_effect = get_side_effect

        client = IstabaiClient()
        with pytest.raises(expected_exception) as api_exception_info:
            await client.login("abc", "")

        assert api_exception_info.value.code == code
        assert api_exception_info.value.message == message


async def test_get_homes_returns() -> None:
    """Test"""
    # TODO fix description?
    with patch("httpx.AsyncClient.get") as get_mock:

        def get_side_effect(url, **kwargs):
            request = httpx.Request("GET", url, **kwargs)
            content = TestData.get_homes_response_json()
            return httpx.Response(200, request=request, json=content)

        get_mock.side_effect = get_side_effect

        client = IstabaiClient()
        homes_response = await client.get_homes()

        assert homes_response is not None

        assert homes_response.homes is not None
        homes = homes_response.homes
        assert len(homes) == 1
        home = homes[0]
        assert home.id == 5
        assert home.name == "The Crumb Matrix"


async def test_get_rooms_returns() -> None:
    """Test"""
    # TODO fix description

    with patch("httpx.AsyncClient.get") as get_mock:

        def get_side_effect(url, **kwargs):
            request = httpx.Request("GET", url, **kwargs)
            content = TestData.get_rooms_response_json()
            return httpx.Response(200, request=request, json=content)

        get_mock.side_effect = get_side_effect

        client = IstabaiClient()
        rooms_response = await client.get_rooms(5)

        assert rooms_response is not None
        rooms = rooms_response.rooms
        assert len(rooms) == 4
        assert rooms[0].id == 201
        # assert rooms[0].
        assert rooms[1].id == 202
        assert rooms[2].id == 203
        assert rooms[3].id == 204

        assert rooms[0].set_temperature.day == 23
        assert rooms[0].set_temperature[TemperatureMode.DAY] == 23

        assert rooms_response.home is not None
        home = rooms_response.home
        assert home.id == 5
        assert home.name == "The Crumb Matrix"


async def test_set_temperature_returns() -> None:
    """Test"""
    # TODO fix description

    with patch("httpx.AsyncClient.get") as get_mock:

        def get_side_effect(url, **kwargs):
            request = httpx.Request("GET", url, **kwargs)
            content = TestData.set_temperature_response_json()
            return httpx.Response(200, request=request, json=content)

        get_mock.side_effect = get_side_effect

        client = IstabaiClient()
        set_temperature_response = await client.set_temperature(
            204, TemperatureMode.ECO, Decimal("17.2")
        )

        assert set_temperature_response is not None
        assert set_temperature_response.set_temperature is not None
        temp_values = set_temperature_response.set_temperature

        assert temp_values.room_id == 204
        assert temp_values.mode == TemperatureMode.ECO
        assert temp_values.temperature == Decimal("17.2")


@pytest.mark.skip("real call disable")
async def test_get_rooms_returns_real() -> None:
    """Test"""
    # TODO fix description

    client = IstabaiClient()
    # TODO remove key and home id
    client._api_key = "cce6ede8a2847491b7a11ba4d4eb474b"
    rooms = await client.get_rooms(2525)


# TODO do I need a test for boos methods?
# TODO do I want to test the parameters I send to the API? probably not, not sure?
# TODO test login with api key ...


@pytest.mark.skip("real call disable")
async def test_set_temperature_returns_real() -> None:
    client = IstabaiClient()
    # TODO remove key and home id
    client._api_key = "cce6ede8a2847491b7a11ba4d4eb474b"
    # result = await client.set_temperature(7629, TemperatureMode.ECO, Decimal('15'))
    result = await client.set_boost_temperature(7629, Decimal("19"), duration=42)
    # result = await client.clear_boost(7629)

    assert result is not None


@pytest.mark.skip("real call disable")
async def test_use_schedules_returns_real() -> None:
    client = IstabaiClient()
    # TODO remove key and home id
    client._api_key = "cce6ede8a2847491b7a11ba4d4eb474b"
    result = await client.use_schedules(7398, True)

    assert result is not None
    assert result.success is True


@pytest.mark.skip("real call disable")
async def test_login_api_key_real() -> None:
    client = IstabaiClient()
    result = await client.login(api_key="cce6ede8a2847491b7a11ba4d4eb474b")

    assert result is not None
    assert result.success is True
    assert result.api_key == "cce6ede8a2847491b7a11ba4d4eb474b"


# TODO use existing session?
