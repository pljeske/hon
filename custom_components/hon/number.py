from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.number import (
    NumberEntity,
    NumberEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTime, UnitOfTemperature
from homeassistant.core import callback
from homeassistant.helpers.entity import EntityCategory
from pyhon.parameter.range import HonParameterRange

from .const import DOMAIN
from .hon import HonEntity, unique_entities


@dataclass
class HonConfigNumberEntityDescription(NumberEntityDescription):
    entity_category: EntityCategory = EntityCategory.CONFIG


@dataclass
class HonNumberEntityDescription(NumberEntityDescription):
    pass


NUMBERS: dict[str, tuple[NumberEntityDescription, ...]] = {
    "AP": (
        HonConfigNumberEntityDescription(
            key="startProgram.machMode",
            name="Wind Speed",
            icon="mdi:wind-sock"
        ),
    ),
    "WM": (
        HonConfigNumberEntityDescription(
            key="startProgram.delayTime",
            name="Delay Time",
            icon="mdi:timer-plus",
            native_unit_of_measurement=UnitOfTime.MINUTES,
            translation_key="delay_time",
        ),
        HonConfigNumberEntityDescription(
            key="startProgram.rinseIterations",
            name="Rinse Iterations",
            icon="mdi:rotate-right",
            translation_key="rinse_iterations",
        ),
        HonConfigNumberEntityDescription(
            key="startProgram.mainWashTime",
            name="Main Wash Time",
            icon="mdi:clock-start",
            native_unit_of_measurement=UnitOfTime.MINUTES,
            translation_key="wash_time",
        ),
        HonConfigNumberEntityDescription(
            key="startProgram.steamLevel",
            name="Steam Level",
            icon="mdi:weather-dust",
            translation_key="steam_level",
        ),
        HonConfigNumberEntityDescription(
            key="startProgram.waterHard",
            name="Water hard",
            icon="mdi:water",
            translation_key="water_hard",
        ),
        HonConfigNumberEntityDescription(
            key="startProgram.lang",
            name="lang",
        ),
    ),
    "TD": (
        HonConfigNumberEntityDescription(
            key="startProgram.delayTime",
            name="Delay time",
            icon="mdi:timer-plus",
            native_unit_of_measurement=UnitOfTime.MINUTES,
            translation_key="delay_time",
        ),
        HonConfigNumberEntityDescription(
            key="startProgram.tempLevel",
            name="Temperature level",
            icon="mdi:thermometer",
            translation_key="tumbledryertemplevel",
        ),
        HonConfigNumberEntityDescription(
            key="startProgram.dryTime",
            name="Dry Time",
            translation_key="dry_time",
        ),
    ),
    "OV": (
        HonConfigNumberEntityDescription(
            key="startProgram.delayTime",
            name="Delay time",
            icon="mdi:timer-plus",
            native_unit_of_measurement=UnitOfTime.MINUTES,
            translation_key="delay_time",
        ),
        HonConfigNumberEntityDescription(
            key="startProgram.tempSel",
            name="Target Temperature",
            icon="mdi:thermometer",
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
            translation_key="target_temperature",
        ),
        HonConfigNumberEntityDescription(
            key="startProgram.prTime",
            name="Program Duration",
            icon="mdi:timelapse",
            native_unit_of_measurement=UnitOfTime.MINUTES,
            translation_key="program_duration",
        ),
    ),
    "IH": (
        HonConfigNumberEntityDescription(
            key="startProgram.temp",
            name="Temperature",
            icon="mdi:thermometer",
            translation_key="temperature",
        ),
        HonConfigNumberEntityDescription(
            key="startProgram.powerManagement",
            name="Power Management",
            icon="mdi:timelapse",
            translation_key="power_management",
        ),
    ),
    "DW": (
        HonConfigNumberEntityDescription(
            key="startProgram.delayTime",
            name="Delay time",
            icon="mdi:timer-plus",
            native_unit_of_measurement=UnitOfTime.MINUTES,
            translation_key="delay_time",
        ),
        HonConfigNumberEntityDescription(
            key="startProgram.waterHard",
            name="Water hard",
            icon="mdi:water",
            translation_key="water_hard",
        ),
    ),
    "AC": (
        HonNumberEntityDescription(
            key="settings.tempSel",
            name="Target Temperature",
            icon="mdi:thermometer",
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
            translation_key="target_temperature",
        ),
    ),
    "REF": (
        HonNumberEntityDescription(
            key="settings.tempSelZ1",
            name="Fridge Temperature",
            icon="mdi:thermometer",
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
            translation_key="fridge_temp_sel",
        ),
        HonNumberEntityDescription(
            key="settings.tempSelZ2",
            name="Freezer Temperature",
            icon="mdi:thermometer",
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
            translation_key="freezer_temp_sel",
        ),
    ),
    "HO": (
        HonNumberEntityDescription(
            key="startProgram.lightStatus",
            name="Light status",
            icon="mdi:lightbulb",
            entity_category=EntityCategory.CONFIG,
        ),
    ),
}

NUMBERS["WD"] = unique_entities(NUMBERS["WM"], NUMBERS["TD"])


async def async_setup_entry(hass, entry: ConfigEntry, async_add_entities) -> None:
    entities = []
    for device in hass.data[DOMAIN][entry.unique_id].appliances:
        for description in NUMBERS.get(device.appliance_type, []):
            if description.key not in device.available_settings:
                continue
            if isinstance(description, HonNumberEntityDescription):
                entity = HonNumberEntity(hass, entry, device, description)
            elif isinstance(description, HonConfigNumberEntityDescription):
                entity = HonConfigNumberEntity(hass, entry, device, description)
            else:
                continue
            await entity.coordinator.async_config_entry_first_refresh()
            entities.append(entity)
    async_add_entities(entities)


class HonNumberEntity(HonEntity, NumberEntity):
    entity_description: HonNumberEntityDescription

    def __init__(self, hass, entry, device, description) -> None:
        super().__init__(hass, entry, device, description)

        self._data = device.settings[description.key]
        if isinstance(self._data, HonParameterRange):
            self._attr_native_max_value = self._data.max
            self._attr_native_min_value = self._data.min
            self._attr_native_step = self._data.step

    @property
    def native_value(self) -> float | None:
        return self._device.get(self.entity_description.key)

    async def async_set_native_value(self, value: float) -> None:
        setting = self._device.settings[self.entity_description.key]
        if isinstance(setting, HonParameterRange):
            setting.value = value
        command = self.entity_description.key.split(".")[0]
        await self._device.commands[command].send()
        await self.coordinator.async_refresh()

    @callback
    def _handle_coordinator_update(self, update=True) -> None:
        setting = self._device.settings[self.entity_description.key]
        if isinstance(setting, HonParameterRange):
            self._attr_native_max_value = setting.max
            self._attr_native_min_value = setting.min
            self._attr_native_step = setting.step
        self._attr_native_value = setting.value
        if update:
            self.async_write_ha_state()

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return (
            super().available
            and self._device.get("remoteCtrValid", "1") == "1"
            and self._device.get("attributes.lastConnEvent.category") != "DISCONNECTED"
        )


class HonConfigNumberEntity(HonNumberEntity):
    entity_description: HonConfigNumberEntityDescription

    async def async_set_native_value(self, value: str) -> None:
        setting = self._device.settings[self.entity_description.key]
        if isinstance(setting, HonParameterRange):
            setting.value = value
        await self.coordinator.async_refresh()

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return super(NumberEntity, self).available
