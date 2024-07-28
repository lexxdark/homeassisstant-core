from datetime import timedelta
from decimal import Decimal
import logging


from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, UnitOfTemperature, STATE_CLASSES, StateType
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, CoordinatorEntity

from .const import DOMAIN, CONF_SELECTED_HOME_LIST
from .istabai_client import IstabaiClient, RoomsResponse

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    """Set up sensors based on a ConfigEntry."""
    api: IstabaiClient = hass.data[DOMAIN][entry.entry_id]

    entities: list[IstabaiTemperatureSensor] = []

    for home_id, home_name in entry.data[CONF_SELECTED_HOME_LIST]:
        coordinator = IstabaiRoomFetchCoordinator(hass, api, home_id)
        # TODO probably we need to organize stuff here
        await coordinator.async_config_entry_first_refresh()
        response: RoomsResponse = coordinator.data
        for room in response.rooms:
            entity = IstabaiTemperatureSensor(coordinator, home_id, room.id)
            entities.append(entity)

    async_add_entities(entities, True)


class IstabaiRoomFetchCoordinator(DataUpdateCoordinator):
    """Istabai room fetch coordinator."""

    _api: IstabaiClient
    _home_id: int

    def __init__(self, hass: HomeAssistant, api: IstabaiClient, home_id: int) -> None:
        """Initialize Istabai Room fetch coordinator"""

        super().__init__(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name="Istabai room",
            # Polling interval. Will only be polled if there are subscribers.
            # TODO figure out refresh interval
            update_interval=timedelta(seconds=60),
        )
        self._api = api
        self._home_id = home_id

    async def _async_update_data(self):
        """Retrieves all rooms from a home"""

        # TODO exception handling
        return await self._api.get_rooms(self._home_id)

class IstabaiTemperatureSensor(CoordinatorEntity, SensorEntity):

    _home_id: int
    _room_id: int
    _temperature: Decimal
    _name: str

    def __init__(self, coordinator: IstabaiRoomFetchCoordinator, home_id: int, room_id: int):
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator)
        self._home_id = home_id
        self._room_id = room_id

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        room: Room = None
        data: RoomsResponse = self.coordinator.data
        for current_room in data.rooms:
            if current_room.id == self._room_id:
                room = current_room
                break

        self._temperature = room.temperature
        self._name = room.name
        self.async_write_ha_state()

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return self._name

    @property
    def device_class(self) -> str:
        """Returns the device class"""
        return SensorDeviceClass.TEMPERATURE

    @property
    def native_unit_of_measurement(self) -> str:
        """Returns the native unit of measurement"""
        return UnitOfTemperature.CELSIUS

    # TODO define state class?

    @property
    def native_value(self) -> Decimal:
        """Returns the temperature in Celsis"""
        return self._temperature

    @@property
    def suggested_display_precision(self) -> int:
        return 1

    # Implement other required properties and methods...
