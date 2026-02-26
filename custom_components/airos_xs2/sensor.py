from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import DeviceInfo
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]

    sensors = [
        AiRXS2Sensor(coordinator, entry, "signal", "dBm"),
        AiRXS2Sensor(coordinator, entry, "noise", "dBm"),
        AiRXS2Sensor(coordinator, entry, "ccq", "%"),
        AiRXS2Sensor(coordinator, entry, "snr", "dB"),
        AiRXS2Sensor(coordinator, entry, "wlanTxRate", "Mbps"),
        AiRXS2Sensor(coordinator, entry, "wlanRxRate", "Mbps"),
    ]

    async_add_entities(sensors)

class AiRXS2Sensor(SensorEntity):
    def __init__(self, coordinator, entry, key, unit):
        self.coordinator = coordinator
        self.key = key
        self._entry = entry
        self._attr_name = f"{entry.data['name']} {key}"
        self._attr_unique_id = f"{entry.data['host']}_{key}"
        self._attr_native_unit_of_measurement = unit

    @property
    def device_info(self):
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.data["host"])},
            name=self._entry.data["name"],
            manufacturer="Ubiquiti",
            model="airOS XS2",
        )

    @property
    def native_value(self):
        return self.coordinator.data.get(self.key)
