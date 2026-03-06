import asyncssh
import logging
from datetime import timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.core import HomeAssistant
from .const import DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


def _to_text(val) -> str:
    if val is None:
        return ""
    if isinstance(val, (bytes, bytearray)):
        return val.decode(errors="ignore")
    return str(val)


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

                # DO NOT use conn.run() — HA/asyncssh updates changed SSHCompletedProcess
                proc = await conn.create_process("mca-status")

                stdout = await proc.stdout.read()
                stderr = await proc.stderr.read()
                await proc.wait()

                out_text = _to_text(stdout)
                err_text = _to_text(stderr)

                # Some firmware prints to stderr even on success; prefer stdout if it has key=value pairs
                output = out_text if "=" in out_text else (err_text if "=" in err_text else out_text)

                if proc.exit_status not in (0, None) and not output.strip():
                    raise UpdateFailed(f"mca-status exit_status={proc.exit_status} stderr={err_text}")

                if "=" not in output:
                    raise UpdateFailed(f"mca-status returned no key=value output. stderr={err_text}")

                return self._parse_output(output)

        except UpdateFailed:
            raise
        except Exception as e:
            raise UpdateFailed(f"SSH error: {e}")

    def _parse_output(self, output: str):
        data = {}
        for line in output.splitlines():
            if "=" in line:
                key, value = line.strip().split("=", 1)
                data[key] = value

        # Keep your existing entities stable
        data["signal"] = float(data.get("signal", 0))
        data["noise"] = float(data.get("noise", 0))
        data["ccq"] = float(data.get("ccq", 0)) / 10
        data["snr"] = data["signal"] - data["noise"]
        data["wlanTxRate"] = float(data.get("wlanTxRate", 0))
        data["wlanRxRate"] = float(data.get("wlanRxRate", 0))

        return data