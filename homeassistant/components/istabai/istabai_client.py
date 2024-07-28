"""Istabai API class, should be separated into its own PYpi"""
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
import pprint
from typing import Optional, Type, TypeVar, Union

import dacite
from httpx import AsyncClient, Response

dbg = pprint.PrettyPrinter(indent=4)


@dataclass
class Schedule:
    """DTO for a specific schedule"""

    id: int
    name: str
    default: bool


@dataclass
class Home:
    """DTO for a specific home"""

    id: int
    name: str
    address: Optional[str]
    boiler: bool
    boiler_delay: bool
    boiler_delay_timeout: str
    # TODO how do I specify arrays
    # features:
    has_boiler: bool
    # location: not sure ...
    notifications: int
    offline_mode: bool
    owner_user_id: int
    rooms: int
    schedules: list[Schedule]
    time_zone: str


class TemperatureMode(Enum):
    DAY = "day"
    NIGHT = "night"
    ECO = "eco"
    TEMP = "temp"
    OFFLINE = "offline"
    BOOST = "boost"

    @classmethod
    def temperature_mode_converter(cls, input_value: str):
        try:
            # Convert the string to uppercase and attempt to match an enum member
            return TemperatureMode[input_value.upper()]
        except KeyError:
            # Handle the case where the value does not match any enum member
            raise ValueError(f"Invalid temperature mode: {input_value}")


@dataclass
class BoostTemperature:
    """Structure describing boost value"""

    is_active: bool
    temperature: Optional[Decimal] = field(default=None)

    @classmethod
    def boot_temperature_converter(
        cls, input_value: Union[bool, float]
    ) -> "BoostTemperature":
        if input_value is False:
            return cls(is_active=False)
        elif isinstance(input_value, float):
            return cls(is_active=True, temperature=Decimal(str(input_value)))
        else:
            raise ValueError(f"Invalid value for BoostTemperature: {input_value}")


# TODO documentation
@dataclass
class BoostUntil:
    is_active: bool
    until: Optional[datetime] = field(default=None)

    @classmethod
    def boot_until_converter(cls, input_value: Union[bool, Decimal]) -> "BoostUntil":
        if input_value is False:
            return cls(is_active=False)
        elif isinstance(input_value, int):
            return cls(is_active=True, until=unix_to_datetime(input_value))
        else:
            raise ValueError(f"Invalid value for BoostTemperature: {input_value}")


@dataclass
class RoomSetTemperatures:
    """DTO for set temperature in a room"""

    day: Decimal
    night: Decimal
    eco: Decimal
    temp: Decimal
    offline: Decimal
    boost: BoostTemperature

    def __getitem__(self, key: TemperatureMode) -> Decimal:
        if key == TemperatureMode.BOOST:
            raise ValueError(
                "Boost temperature can't be accessed through the dictionary method"
            )

        return getattr(self, key.value)


@dataclass
class IstabaiDeviceInfo:
    """Device information for an Istabai Room"""

    faulty: bool
    battery: Decimal
    charging: bool
    signal: Decimal
    last_data: datetime


@dataclass
class Room:
    """DTO for a specific Room"""

    id: int
    read_only: bool
    name: str
    temperature: Decimal
    min_temperature: Decimal
    max_temperature: Decimal
    set_temperature: RoomSetTemperatures
    humidity: int
    device: IstabaiDeviceInfo
    last_motion: Optional[datetime]
    has_motion_sensor: bool
    is_water: bool
    on_schedule: bool
    boost_until: BoostUntil
    boost_until_normal: BoostUntil
    # TODO mode deserialization
    active_schedule_id: int


@dataclass
class SetTemperature:
    """Defines the details of a set temperature call"""

    room_id: int
    mode: TemperatureMode
    temperature: Decimal


@dataclass
class AuthenticatedUser:
    """Represent the currently authenticated user"""

    id: int
    name: str
    lang: str
    api_key: str
    homes: int


@dataclass
class LoginResponse:
    """DTO for"""

    timestamp: datetime
    user: AuthenticatedUser
    homes: list[Home]


@dataclass
class LoginResult:
    """Indicates if a call to authenticate was successful or not"""

    success: bool
    api_key: Optional[str]
    full_response: Optional[LoginResponse]


@dataclass
class HomesResponse:
    """DTO for homes response"""

    timestamp: datetime
    homes: list[Home]
    # Left for further improvement home_invitations


@dataclass
class RoomsResponse:
    """DTO response for the rooms request"""

    timestamp: datetime
    rooms: list[Room]
    home: Home
    home_count: int


@dataclass
class SetTemperatureResponse:
    """The response from the set temperature call"""

    set_temperature: SetTemperature


@dataclass
class UseSchedulesResponse:
    """The response from a use schedules call"""

    success: bool


def unix_to_datetime(value: int) -> datetime:
    """Deserializes unix time stamp to datetime"""

    return datetime.fromtimestamp(value)


def float_to_decimal(value: float) -> Decimal:
    """Deserializes to decimal"""

    return Decimal(str(value))


# TODO try to provide the error from the API?
class IstabaiError(Exception):
    """All Istabai errors are derived from this"""


class IstabaiInvalidApiKey(IstabaiError):
    """Exception raised when the API key is invalid"""


class IstabaiInvalidApiUsage(IstabaiError):
    """Exception used when using the API calls in a wrong way"""

    def __init__(self, message):
        super().__init__(message)
        self.message = message


class IstabaiUnavailable(IstabaiError):
    """Exception raised when the API service is temporarily done"""


class IstabaiInvalidRequest(IstabaiError):
    """Exception raised when the API service replies that we are missing parameters"""


class IstabaiUnexpectedResponse(IstabaiError):
    """Exception raised when the API responded in an unexpected way"""


class IstabaiUnexpectedStatusCode(IstabaiUnexpectedResponse):
    """Exception raised when the API provided an unexpected http status code"""

    code: int
    message: str

    def __init__(self, code: int, message: str):
        super().__init__(f"Unexpected status code {code}")
        self.code = code
        self.message = message


class IstabaiInvalidUsernameOrPassword(IstabaiError):
    """Exception raised when the authentication details are invalid"""


class IstabaiGenericError(IstabaiError):
    """Exception raised when we get an error code that we don't know from Istabai"""

    code: int
    message: str

    def __init__(self, code: int, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


T = TypeVar("T")


class IstabaiClient:
    """API client class"""

    _base_url: str
    _api_key: str = None

    def __init__(self, base_url: str = "https://api.istabai.com") -> None:
        self._base_url = base_url
        self.session = AsyncClient(
            # TODO comment
            # event_hooks={"request": [log_request], "response": [log_response]}
        )

    # TODO login seems to work with an api key directly as well we should probably implement it

    async def login(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> LoginResult:
        """Authenticates to the API and stores the api key"""

        try:
            if api_key is not None and (username is not None or password is not None):
                raise IstabaiInvalidApiUsage(
                    "Either send api_key or credentials not both"
                )
            if api_key is None and username is None and password is None:
                raise IstabaiInvalidApiUsage(
                    "You must send either the credentials or the api key"
                )
            if api_key is None and (username is None or password is None):
                raise IstabaiInvalidApiUsage(
                    "When sending the credentials you must provide both the username and password"
                )

            if api_key is not None:
                params = {"api_key": api_key}
            elif username is not None and password is not None:
                params = {"email": username, "password": password}
            else:
                raise Exception(
                    "Unexpected situation, should have been handled by validation"
                )

            url = f"{self._base_url}/2/login.json"
            response = await self.session.get(url, params=params)
            login_response = self._check_for_errors_and_deserialize(
                response, data_class=LoginResponse
            )

            result = LoginResult(
                success=True,
                api_key=login_response.user.api_key,
                full_response=login_response,
            )
            self._api_key = result.api_key
            return result
        except IstabaiInvalidUsernameOrPassword:
            return LoginResult(success=False, api_key=None, full_response=None)

    async def get_homes(self) -> HomesResponse:
        """Gets the lists of homes. Login must be called before this"""

        params = {"api_key": self._api_key}

        url = f"{self._base_url}/2/homes.list.json"
        response = await self.session.get(
            url,
            params=params,
        )

        return self._check_for_errors_and_deserialize(
            response, data_class=HomesResponse
        )

    async def get_rooms(self, home_id: int) -> RoomsResponse:
        """Gets the list of rooms"""

        params = {"api_key": self._api_key, "home_id": home_id}

        url = f"{self._base_url}/2/rooms.list.json"
        response = await self.session.get(url, params=params)
        return self._check_for_errors_and_deserialize(
            response, data_class=RoomsResponse
        )

    async def set_temperature(
        self, room_id: int, mode: TemperatureMode, temperature: Decimal
    ) -> SetTemperatureResponse:
        """Sets the list of temperatures"""
        return await self._set_temperature(room_id, mode, temperature)

    async def set_boost_temperature(
        self, room_id: int, temperature: Decimal, duration: int
    ) -> SetTemperatureResponse:
        return await self._set_temperature(
            room_id, TemperatureMode.BOOST, temperature, duration
        )

    async def clear_boost(self, room_id: int) -> SetTemperatureResponse:
        return await self._set_temperature(
            room_id, TemperatureMode.BOOST, Decimal(1), 0
        )

    async def use_schedules(
        self, room_id: int, use_schedules: bool
    ) -> UseSchedulesResponse:
        params = {
            "api_key": self._api_key,
            "room_id": room_id,
            "use_schedule": 1 if use_schedules else 0,
        }

        url = f"{self._base_url}/2/rooms.use_schedule.json"
        response = await self.session.get(url, params=params)
        return self._check_for_errors_and_deserialize(
            response, data_class=UseSchedulesResponse
        )

    async def _set_temperature(
        self,
        room_id: int,
        mode: TemperatureMode,
        temperature: Decimal,
        duration: Optional[int] = None,
    ) -> SetTemperatureResponse:
        if mode == TemperatureMode.BOOST and duration is None:
            raise IstabaiInvalidApiUsage("Boot mode requires a duration")

        if mode != TemperatureMode.BOOST and duration is not None:
            raise IstabaiInvalidApiUsage(
                "Duration not allowed in any other mode than boost"
            )

        params = {
            "api_key": self._api_key,
            "room_id": room_id,
            "temperature": temperature,
            "mode": mode.value.upper(),
        }

        if duration is not None:
            params["duration"] = duration

        url = f"{self._base_url}/2/rooms.set_temperature.json"
        response = await self.session.get(url, params=params)
        return self._check_for_errors_and_deserialize(
            response, data_class=SetTemperatureResponse
        )

    def _check_for_errors_and_deserialize(self, response, data_class: Type[T]) -> T:
        url = response.request.url
        print(f"Response for {url}")
        print(f"Status code: {response.status_code}")
        print(response.text)
        print("----------")

        self._assert_status_code(response)
        json = self._assert_json_without_errors(response)

        config = dacite.Config(
            type_hooks={
                datetime: unix_to_datetime,
                Decimal: float_to_decimal,
                BoostTemperature: BoostTemperature.boot_temperature_converter,
                BoostUntil: BoostUntil.boot_until_converter,
                TemperatureMode: TemperatureMode.temperature_mode_converter,
            }
        )
        return dacite.from_dict(data_class=data_class, data=json, config=config)

    async def get_heater_status(self, home_id: str, room_id: str) -> any:
        """Get the  heater status"""

        headers = {"Authorization": f"Bearer {self._api_key}"}
        url = f"{self._base_url}/homes/{home_id}/rooms/{room_id}/heater"
        response = await self.session.get(url, headers=headers)
        if response.status_code != 200:
            raise IstabaiError(response.json())
        return response.json()

    @staticmethod
    def _assert_status_code(response: Response) -> None:
        """Raises the proper error depending on the HTTP status code"""

        status_code: int = response.status_code

        if status_code == 300:
            raise IstabaiInvalidApiKey(response.text)
        if status_code == 100:
            raise IstabaiUnavailable(response.text)
        if status_code == 203:
            raise IstabaiInvalidRequest(response.text)
        if status_code != 200:
            raise IstabaiUnexpectedStatusCode(status_code, response.text)

    @staticmethod
    def _assert_json_without_errors(response: Response) -> any:
        """Parses the response as JSON and verifies that it's not an error response"""

        if response.headers["content-type"] != "application/json":
            raise IstabaiUnexpectedResponse()

        json = response.json()

        if "error" in json:
            code = json["error"].get("code", "unknown")
            message = json["error"].get("description", "unknown")
            if code == 401:
                raise IstabaiInvalidUsernameOrPassword(message)
            raise IstabaiGenericError(code, message)

        return json

    # async def set_heater_status(self, home_id: str, room_id: str, status: bool) -> any:
    #     headers = {
    #         "Authorization": f"Bearer {self.api_key}",
    #         "Content-Type": "application/json",
    #     }
