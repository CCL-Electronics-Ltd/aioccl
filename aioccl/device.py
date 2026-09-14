"""CCL device mapping."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import TypedDict

from .exception import CCLDataUpdateException
from .sensor import CCLSensor

_LOGGER = logging.getLogger(__name__)

CCL_DEVICE_INFO_TYPES = ("serial_no", "mac_address", "model", "fw_ver")


class CCLDevice:
    """Mapping for a CCL device."""

    def __init__(self, passkey: str):
        """Initialize a CCL device."""

        class Info(TypedDict):
            """Store device information."""
            fw_ver: str | None
            last_update_time: float | None
            mac_address: str | None
            model: str | None
            passkey: str
            serial_no: str | None


        self._info: Info = {
            "fw_ver": None,
            "last_update_time": None,
            "mac_address": None,
            "model": None,
            "passkey": passkey,
            "serial_no": None,
        }

        self._data: dict[str, dict[str, CCLSensor]] = {
            "SENSOR": {},
            "BINARY_SENSOR": {},
        }
        self._update_callback: Callable[[dict[str, dict[str, CCLSensor]]], None] | None = None

        self._new_sensors: list[CCLSensor] | None = []
        self._new_sensor_callback: Callable[[], None] | None = None

    @property
    def passkey(self) -> str:
        """Return the passkey."""
        return self._info["passkey"]

    @property
    def device_id(self) -> str | None:
        """Return the device ID."""
        if self.mac_address is None:
            return None
        return self.mac_address.replace(":", "").lower()[-6:]

    @property
    def last_update_time(self) -> float | None:
        """Return the last update time."""
        return self._info["last_update_time"]

    @property
    def name(self) -> str | None:
        """Return the display name."""
        if self.device_id is not None:
            return self.model + " - " + self.device_id
        return self._info["model"]

    @property
    def mac_address(self) -> str | None:
        """Return the MAC address."""
        return self._info["mac_address"]

    @property
    def model(self) -> str | None:
        """Return the model."""
        return self._info["model"]

    @property
    def fw_ver(self) -> str | None:
        """Return the firmware version."""
        return self._info["fw_ver"]

    def get_data(self) -> dict[str, dict[str, CCLSensor]]:
        """Get all types of sensor data under this device."""
        if self._info["last_update_time"] is None:
            raise CCLDataUpdateException("Device is offline or not ready")
        if (
            not any(self._data.values())
            or time.monotonic() - self._info["last_update_time"] > 600
        ):
            raise CCLDataUpdateException("Device is offline or not ready")
        return self._data
    
    def set_update_callback(
        self, callback: Callable[[dict[str, dict[str, CCLSensor]]], None]
    ) -> None:
        """Set the callback function to update sensor data."""
        self._update_callback = callback
        
    def set_new_sensor_callback(self, callback: Callable[[], None]) -> None:
        """Set the callback function to add a new sensor."""
        self._new_sensor_callback = callback


    def update_info(self, new_info: dict[str, None | str]) -> None:
        """Add or update device info."""
        for key, value in new_info.items():
            if key in self._info:
                self._info[key] = str(value)
        self._info["last_update_time"] = time.monotonic()

    def push_updates(self) -> None:
        """Push sensor updates."""
        if self._publish_new_sensors() is True:
            _LOGGER.debug(
                "Added new sensors for device %s at %s.",
                self.device_id,
                self.last_update_time,
            )

        self._publish_updates()
        _LOGGER.debug(
            "Updating sensor data for device %s at %s.",
            self.device_id,
            self.last_update_time,
        )
        
    def process_data(self, data: dict[str, None | str | int | float]) -> None:
        """Add or update all sensor values."""
        for key, value in data.items():
            sensor = next(
                (
                    sensors[key]
                    for sensors in self._data.values()
                    if key in sensors
                ),
                None,
            )
            if sensor is None:
                sensor = CCLSensor(key)
                bucket = "BINARY_SENSOR" if sensor.binary else "SENSOR"
                self._data[bucket][key] = sensor
                self._new_sensors.append(sensor)
            sensor.last_update_time = time.monotonic()
            sensor.value = value
        self.push_updates()

    def _publish_updates(self) -> None:
        """Call the function to update sensor data."""
        try:
            self._update_callback(self._data)
        except Exception as err:  # pylint: disable=broad-exception-caught
            _LOGGER.warning(
                "Error while updating sensors for device %s: %s",
                self.device_id,
                err,
            )

    def _publish_new_sensors(self) -> bool | None:
        """Schedule all registered callbacks to add new sensors."""
        try:
            assert self._new_sensor_callback is not None
            if self._new_sensor_callback(self._new_sensors) is not True:
                raise CCLDataUpdateException("Failed to publish new sensor")
        except Exception:  # pylint: disable=broad-exception-caught
            return None
        return True