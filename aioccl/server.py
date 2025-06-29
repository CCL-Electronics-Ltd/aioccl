"""CCL API server and handler."""

from __future__ import annotations

from http import HTTPStatus
import logging

from aiohttp import web

from .device import CCLDevice, CCL_DEVICE_INFO_TYPES
from .exception import CCLDeviceRegistrationException
from .sensor import CCL_SENSORS

_LOGGER = logging.getLogger(__name__)


class CCLServer:
    """Represent a CCL server manager."""

    LISTEN_PORT = 42373

    devices: dict[str, CCLDevice] = {}

    @staticmethod
    def register(device: CCLDevice) -> None:
        """Register a device with a passkey."""
        if CCLServer.devices.get(device.passkey, None) is not None:
            raise CCLDeviceRegistrationException("Device already exists")
        CCLServer.devices[device.passkey] = device
        _LOGGER.debug("Device registered: %s", device.passkey)

    @staticmethod
    async def handler(request: web.BaseRequest | web.Request) -> web.Response:
        """Handle POST requests for data updating."""
        body: dict[str, None | str | int | float] = {}
        data: dict[str, None | str | int | float] = {}
        device: CCLDevice = None
        info: dict[str, None | str] = {}
        passkey: str = ""
        status: None | int = None
        text: None | str = None

        _LOGGER.debug("Request received: %s", passkey)
        try:
            passkey = request.path[-8:]
            for ref_passkey, ref_device in CCLServer.devices.items():
                if passkey == ref_passkey:
                    device = ref_device
                    break
            assert isinstance(device, CCLDevice), HTTPStatus.NOT_FOUND

            assert request.content_type == "application/json", HTTPStatus.BAD_REQUEST
            assert 0 < request.content_length <= 5000, HTTPStatus.BAD_REQUEST

            body = await request.json()

        except Exception as err:  # pylint: disable=broad-exception-caught
            status = err.args[0]
            if status == HTTPStatus.BAD_REQUEST:
                text = "400 Bad Request."
            elif status == HTTPStatus.NOT_FOUND:
                text = "404 Not Found."
            else:
                status = HTTPStatus.INTERNAL_SERVER_ERROR
                text = "500 Internal Server Error."
            _LOGGER.debug("Request exception occured: %s", err)
            return web.Response(status=status, text=text)

        for key, value in body.items():
            if key in CCL_DEVICE_INFO_TYPES:
                info.setdefault(key, value)
            elif key in CCL_SENSORS:
                data.setdefault(key, value)

        device.update_info(info)
        device.process_data(data)
        status = HTTPStatus.OK
        text = "200 OK"
        _LOGGER.debug("Request processed: %s", passkey)
        return web.Response(status=status, text=text)

    app = web.Application()
    app.add_routes([web.get("/{passkey}", handler)])
    runner = web.AppRunner(app)

    @staticmethod
    async def run() -> None:
        """Try to run the API server."""
        try:
            _LOGGER.debug("Trying to start the API server.")
            await CCLServer.runner.setup()
            site = web.TCPSite(CCLServer.runner, port=CCLServer.LISTEN_PORT)
            await site.start()
        except Exception as err:  # pylint: disable=broad-exception-caught
            _LOGGER.warning("Failed to run the API server: %s", err)
        else:
            _LOGGER.debug("Successfully started the API server.")

    @staticmethod
    async def stop() -> None:
        """Stop running the API server."""
        await CCLServer.runner.cleanup()
