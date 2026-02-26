import asyncssh
import logging
from datetime import timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.core import HomeAssistant
from .const import DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)

class AiRXS2Coordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, host, username, password, name):
        self.host = host
        self.username = username
        self.password = password
        self.device_name = name

        super().__init__(
            hass,
            logger=_LOGGER,
            name=f"airos_xs2_{name}",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )

    async def _async_update_data(self):
        try:
            async with asyncssh.connect(
                self.host,
                username=self.username,
                password=self.password,
                known_hosts=None,
                kex_algs=["diffie-hellman-group1-sha1"],
                encryption_algs=["aes128-cbc"],
                server_host_key_algs=["ssh-rsa"],
            ) as conn:

                result = await conn.run("mca-status", check=True)
                return self._parse_output(result.stdout)

        except Exception as e:
            raise UpdateFailed(f"SSH error: {e}")

    def _parse_output(self, output):
        data = {}
        for line in output.splitlines():
            if "=" in line:
                key, value = line.strip().split("=", 1)
                data[key] = value

        data["signal"] = float(data.get("signal", 0))
        data["noise"] = float(data.get("noise", 0))
        data["ccq"] = float(data.get("ccq", 0)) / 10
        data["snr"] = data["signal"] - data["noise"]

        data["wlanTxRate"] = float(data.get("wlanTxRate", 0))
        data["wlanRxRate"] = float(data.get("wlanRxRate", 0))

        return data
