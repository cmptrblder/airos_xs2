import asyncssh
from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.entity import DeviceInfo
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([AiRXS2RebootSwitch(coordinator, entry)])

class AiRXS2RebootSwitch(SwitchEntity):
    def __init__(self, coordinator, entry):
        self.coordinator = coordinator
        self._entry = entry
        self._attr_name = f"{entry.data['name']} Reboot"
        self._attr_unique_id = f"{entry.data['host']}_reboot"

    @property
    def device_info(self):
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.data["host"])},
            name=self._entry.data["name"],
            manufacturer="Ubiquiti",
            model="airOS XS2",
        )

    async def async_turn_on(self, **kwargs):
        async with asyncssh.connect(
            self.coordinator.host,
            username=self.coordinator.username,
            password=self.coordinator.password,
            known_hosts=None,
            kex_algs=["diffie-hellman-group1-sha1"],
            encryption_algs=["aes128-cbc"],
            server_host_key_algs=["ssh-rsa"],
        ) as conn:
            await conn.run("reboot")

    async def async_turn_off(self, **kwargs):
        pass

    @property
    def is_on(self):
        return False
