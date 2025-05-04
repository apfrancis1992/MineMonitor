"""Config flow for MineMonitor integration."""
from __future__ import annotations

import logging
import voluptuous as vol
import aiohttp
import asyncio
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from homeassistant import config_entries
from homeassistant.const import (
    CONF_HOST,
    CONF_PORT,
    CONF_NAME,
    CONF_SCAN_INTERVAL,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from . import DOMAIN, CONF_BTC_ADDRESSES, DEFAULT_PORT, DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)

class MinemonitorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Bitcoin Mining."""

    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            port = user_input.get(CONF_PORT, DEFAULT_PORT)
            
            # Check if already configured
            await self.async_set_unique_id(f"{host}:{port}")
            self._abort_if_unique_id_configured()

            # Process and validate BTC addresses
            btc_addresses_str = user_input[CONF_BTC_ADDRESSES]
            btc_addresses = [addr.strip() for addr in btc_addresses_str.split(",")]
            
            # Update user_input with the list of BTC addresses
            user_input[CONF_BTC_ADDRESSES] = btc_addresses
            
            # Validate connection and BTC addresses
            try:
                await self._test_connection(host, port, btc_addresses)
                return self.async_create_entry(
                    title=f"Mining Server at {host}:{port}",
                    data=user_input,
                )
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidBTCAddress:
                errors["base"] = "invalid_btc_address"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        # Show form
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): str,
                    vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
                    vol.Required(CONF_BTC_ADDRESSES): str,  # Comma-separated list
                    vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): int,
                }
            ),
            errors=errors,
        )

    @staticmethod
    async def _test_connection(host: str, port: int, btc_addresses: List[str]) -> None:
        """Test connection to the server and verify BTC addresses."""
        # Simple validation of BTC addresses (very basic check)
        for addr in btc_addresses:
            if not addr.startswith(("1", "3", "bc1")) or len(addr) < 26 or len(addr) > 42:
                raise InvalidBTCAddress
        
        session = aiohttp.ClientSession()
        try:
            # Try to connect to the info endpoint first to verify server connectivity
            url = f"http://{host}:{port}/api/info"
            async with session.get(url, timeout=10) as response:
                if response.status != 200:
                    raise CannotConnect
                
            # Try to query at least one BTC address to verify it's valid and accessible
            url = f"http://{host}:{port}/api/client/{btc_addresses[0]}"
            async with session.get(url, timeout=10) as response:
                if response.status != 200:
                    raise InvalidBTCAddress
                
        except (aiohttp.ClientError, asyncio.TimeoutError):
            raise CannotConnect
        finally:
            await session.close()

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow for this handler."""
        return BitcoinMiningOptionsFlow(config_entry)


class BitcoinMiningOptionsFlow(config_entries.OptionsFlow):
    """Handle Bitcoin Mining options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            # Process comma-separated BTC addresses
            if CONF_BTC_ADDRESSES in user_input:
                btc_addresses = user_input[CONF_BTC_ADDRESSES]
                if isinstance(btc_addresses, str):
                    user_input[CONF_BTC_ADDRESSES] = [
                        addr.strip() for addr in btc_addresses.split(",")
                    ]

            return self.async_create_entry(title="", data=user_input)

        # Prepare BTC addresses for display
        btc_addresses = self.config_entry.data.get(CONF_BTC_ADDRESSES, [])
        if isinstance(btc_addresses, list):
            btc_addresses_str = ", ".join(btc_addresses)
        else:
            btc_addresses_str = btc_addresses

        options = {
            vol.Required(
                CONF_BTC_ADDRESSES, default=btc_addresses_str
            ): str,
            vol.Optional(
                CONF_SCAN_INTERVAL,
                default=self.config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
            ): int,
        }

        return self.async_show_form(step_id="init", data_schema=vol.Schema(options))


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidBTCAddress(HomeAssistantError):
    """Error to indicate an invalid BTC address."""
