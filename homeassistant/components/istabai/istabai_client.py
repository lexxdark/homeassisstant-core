"""Isstabai API class, should be separated into it's own PYpi"""
import pprint
import dacite
from dataclasses import dataclass
from httpx import AsyncClient, Response
import httpx
from typing import List

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
    address: str
    boiler: bool
    boiler_delay: bool
    boiler_delay_timeout: int
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


@dataclass
class AuthenticatedUser:
    """Represent the currently authenticated user"""

    id: int
    name: str
    lang: str
    api_key: str
    homes: int


@dataclass
class HomesResponse:
    """DTO for homes response"""

    homes: list[Home]
    user: AuthenticatedUser


@dataclass
class LoginResponse:
    """DTO for"""

    home: list[Home]


# TODO try to provide the error from the API?
class IstabaiError(Exception):
    """All Istabai errors are derrived from this"""


class IstabaiInvalidApiKey(IstabaiError):
    """Exception raised when the API key is invalid"""


class IstabaiUnavailble(IstabaiError):
    """Exception raised when the API service is temporarily done"""


class IstabaiInvalidRequest(IstabaiError):
    """Exception raised when the API service replies that we are missing parameters"""


class IstabaiUnexpectedResponse(IstabaiError):
    """Exception raised when the API responded in an unexpected way"""


class IstabaiUnexpectedStatusCode(IstabaiUnexpectedResponse):
    """Exception raised when the API provided an unexpected http status code"""


class IstabaiInvalidUsernameOrPassword(IstabaiError):
    """Exception raised when the authentication details are invalid"""


class IstabaiGenericError(IstabaiError):
    """Exception raised when we get an error code that we don't know from Istabai"""


class IstabaiClient:
    """API client class"""

    base_url: str
    username: str
    password: str
    api_key: str = None

    def __init__(
        self, username: str, password: str, base_url: str = "https://api.istabai.com"
    ) -> None:
        self.username = username
        self.password = password
        self.base_url = base_url
        self.session = AsyncClient(
            # TODO comment
            # event_hooks={"request": [log_request], "response": [log_response]}
        )

    async def login(self) -> bool:
        """Authenticates to the API and stores the api key"""

        try:
            url = f"{self.base_url}/2/login.json"
            params = {"email": self.username, "password": self.password}
            response = await self.session.get(url, params=params)
            self.assert_status_code(response)
            json = self.assert_json_without_errors(response)

            print(f"Response for {url}")
            print(f"Status code: {response.status_code}")
            print(response.text)
            print("----------")
            dbg.pprint(json)
            self.api_key = json["user"]["api_key"]
            return True
        except IstabaiInvalidUsernameOrPassword:
            return False

    async def get_homes(self) -> HomesResponse:
        """Gets the lists of homes. Login must be called before this"""

        params = {"api_key": self.api_key}

        url = f"{self.base_url}/2/homes.list.json"
        response = await self.session.get(
            url,
            params=params,
        )
        if response.status_code != 200:
            raise IstabaiError(response.text)
        print(f"Response for {url}")
        print(response.text)
        print("----------")
        dbg.pprint(response.text)
        json = response.json()
        homes = dacite.from_dict(data_class=HomesResponse, data=json)
        return homes

    async def get_rooms(self, home_id: str) -> any:
        """Gets the list of rooms"""

        headers = {"Authorization": f"Bearer {self.api_key}"}
        url = f"{self.base_url}/homes/{home_id}/rooms"
        response = await self.session.get(url, headers=headers)
        if response.status_code != 200:
            raise IstabaiError(response.json())
        return response.json()

    async def get_temperature(self, home_id: str, room_id: str) -> any:
        """Gets the temperature"""

        headers = {"Authorization": f"Bearer {self.api_key}"}
        url = f"{self.base_url}/homes/{home_id}/rooms/{room_id}/temperature"
        response = await self.session.get(url, headers=headers)
        if response.status_code != 200:
            raise IstabaiError(response.json())
        return response.json()

    async def set_temperature(
        self, home_id: str, room_id: str, temperature: float
    ) -> any:
        """Sets the list of temperatures"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        data = {"temperature": temperature}
        url = f"{self.base_url}/homes/{home_id}/rooms/{room_id}/temperature"
        response = await self.session.put(url, headers=headers, json=data)
        if response.status_code != 200:
            raise IstabaiError(response.json())
        return response.json()

    async def get_heater_status(self, home_id: str, room_id: str) -> any:
        """Get the  heater status"""

        headers = {"Authorization": f"Bearer {self.api_key}"}
        url = f"{self.base_url}/homes/{home_id}/rooms/{room_id}/heater"
        response = await self.session.get(url, headers=headers)
        if response.status_code != 200:
            raise IstabaiError(response.json())
        return response.json()

    @staticmethod
    def assert_status_code(response: Response) -> None:
        """Raisese the proper error depending on the HTTP status code"""

        status_code: int = response.status_code

        url = response.request.url
        print(f"Response for {url}")
        print(f"Status code: {response.status_code}")
        print(response.text)
        print("----------")
        # error_code = "unknown"
        # error_description = ""

        if status_code == 300:
            raise IstabaiInvalidApiKey(response.text)
        if status_code == 100:
            raise IstabaiUnavailble(response.text)
        if status_code == 203:
            raise IstabaiInvalidRequest(response.text)
        if status_code != 200:
            raise IstabaiUnexpectedStatusCode(status_code, response.text)

    @staticmethod
    def assert_json_without_errors(response: Response) -> any:
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
