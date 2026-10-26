"""Sensor platform for Karlsruhe Trinkwasser."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, PAGE_URL, SENSOR_KEYS, SENSOR_LIMITS, SENSOR_META
from .coordinator import TrinkwasserCoordinator

_DEVICE_CLASS_MAP = {
    "temperatur": SensorDeviceClass.TEMPERATURE,
}

_STATUS_COLOR = {"OK": "green", "Warnung": "amber", "Kritisch": "red"}


def _calc_status(key: str, value: float) -> str:
    limits = SENSOR_LIMITS.get(key, {})
    if limits.get("limit_min") is not None and value < limits["limit_min"]:
        return "Kritisch"
    if limits.get("limit_max") is not None and value > limits["limit_max"]:
        return "Kritisch"
    if limits.get("warn_min") is not None and value < limits["warn_min"]:
        return "Warnung"
    if limits.get("warn_max") is not None and value > limits["warn_max"]:
        return "Warnung"
    return "OK"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: TrinkwasserCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [TrinkwasserSensor(coordinator, entry, key) for key in SENSOR_KEYS]
    entities.append(TrinkwasserTimestampSensor(coordinator, entry))
    async_add_entities(entities)


class TrinkwasserSensor(CoordinatorEntity[TrinkwasserCoordinator], SensorEntity):
    """One water quality measurement."""

    _attr_has_entity_name = True
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 2

    def __init__(
        self,
        coordinator: TrinkwasserCoordinator,
        entry: ConfigEntry,
        key: str,
    ) -> None:
        super().__init__(coordinator)
        meta = SENSOR_META[key]
        self._key = key
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_name = meta["name"]
        self._attr_native_unit_of_measurement = meta["unit"]
        self._attr_icon = meta["icon"]
        self._attr_device_class = _DEVICE_CLASS_MAP.get(key)
        self._attr_device_info = _device_info(entry)

    @property
    def native_value(self) -> float | None:
        return self.coordinator.data.get(self._key)

    @property
    def extra_state_attributes(self) -> dict:
        attrs: dict = {}
        limits = SENSOR_LIMITS.get(self._key, {})
        if grenzwert := limits.get("grenzwert"):
            attrs["grenzwert"] = grenzwert
        value = self.native_value
        if value is not None:
            status = _calc_status(self._key, value)
            attrs["status"] = status
            attrs["status_color"] = _STATUS_COLOR[status]
        return attrs


class TrinkwasserTimestampSensor(CoordinatorEntity[TrinkwasserCoordinator], SensorEntity):
    """Last-query timestamp published by Stadtwerke."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:clock-outline"

    def __init__(self, coordinator: TrinkwasserCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_timestamp"
        self._attr_name = "Letzte Abfrage"
        self._attr_device_info = _device_info(entry)

    @property
    def native_value(self) -> str | None:
        return self.coordinator.data.get("timestamp")


def _device_info(entry: ConfigEntry) -> DeviceInfo:
    return DeviceInfo(
        entry_type=DeviceEntryType.SERVICE,
        identifiers={(DOMAIN, entry.entry_id)},
        name="Karlsruhe Trinkwasser",
        manufacturer="Stadtwerke Karlsruhe",
        model="Wasserqualität Online-Monitor",
        configuration_url=PAGE_URL,
    )
