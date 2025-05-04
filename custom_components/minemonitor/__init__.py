"""
MineMonitor integration for Home Assistant.
"""
import asyncio
import logging
import aiohttp
import async_timeout
import voluptuous as vol
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    CONF_RESOURCES,
    Platform
)
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryNotReady, HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.service import async_register_admin_service
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

_LOGGER = logging.getLogger(__name__)

# Constants
DOMAIN = "minemonitor"
DEFAULT_PORT = 3334
DEFAULT_SCAN_INTERVAL = 60  # seconds
CONF_BTC_ADDRESSES = "btc_addresses"

# Supported sensor platforms
PLATFORMS = [Platform.SENSOR]

# Configuration schema
CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_HOST): cv.string,
                vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
                vol.Required(CONF_BTC_ADDRESSES): vol.All(cv.ensure_list, [cv.string]),
                vol.Optional(
                    CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                ): cv.positive_int,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Bitcoin Mining component."""
    hass.data.setdefault(DOMAIN, {})
    
    # Register services
    async def refresh_data_service(call: ServiceCall) -> None:
        """Service to force an immediate update of the data."""
        config_entry_id = call.data.get("config_entry_id")
        
        if config_entry_id:
            if config_entry_id in hass.data[DOMAIN]:
                coordinator = hass.data[DOMAIN][config_entry_id]
                await coordinator.async_refresh()
                _LOGGER.debug("Manually refreshed data for entry %s", config_entry_id)
            else:
                _LOGGER.error("Config entry ID %s not found", config_entry_id)
        else:
            # Refresh all entries
            for entry_id, coordinator in hass.data[DOMAIN].items():
                await coordinator.async_refresh()
            _LOGGER.debug("Manually refreshed data for all entries")
    
    async def add_btc_address_service(call: ServiceCall) -> None:
        """Service to add a new Bitcoin address to monitor."""
        config_entry_id = call.data["config_entry_id"]
        btc_address = call.data["btc_address"]
        
        if config_entry_id not in hass.data[DOMAIN]:
            _LOGGER.error("Config entry ID %s not found", config_entry_id)
            return
            
        entry = hass.config_entries.async_get_entry(config_entry_id)
        if not entry:
            _LOGGER.error("Config entry ID %s not found", config_entry_id)
            return
            
        # Get current addresses
        current_addresses = list(entry.data.get(CONF_BTC_ADDRESSES, []))
        
        # Check if address already exists
        if btc_address in current_addresses:
            _LOGGER.warning("Bitcoin address %s already exists", btc_address)
            return
            
        # Add new address
        current_addresses.append(btc_address)
        
        # Update config entry
        new_data = dict(entry.data)
        new_data[CONF_BTC_ADDRESSES] = current_addresses
        hass.config_entries.async_update_entry(entry, data=new_data)
        
        # Reload the entry to apply changes
        await hass.config_entries.async_reload(config_entry_id)
        _LOGGER.info("Added Bitcoin address %s to entry %s", btc_address, config_entry_id)
    
    async def remove_btc_address_service(call: ServiceCall) -> None:
        """Service to remove a Bitcoin address from monitoring."""
        config_entry_id = call.data["config_entry_id"]
        btc_address = call.data["btc_address"]
        
        if config_entry_id not in hass.data[DOMAIN]:
            _LOGGER.error("Config entry ID %s not found", config_entry_id)
            return
            
        entry = hass.config_entries.async_get_entry(config_entry_id)
        if not entry:
            _LOGGER.error("Config entry ID %s not found", config_entry_id)
            return
            
        # Get current addresses
        current_addresses = list(entry.data.get(CONF_BTC_ADDRESSES, []))
        
        # Check if address exists
        if btc_address not in current_addresses:
            _LOGGER.warning("Bitcoin address %s does not exist in entry %s", 
                           btc_address, config_entry_id)
            return
            
        # Remove address
        current_addresses.remove(btc_address)
        
        # Ensure we have at least one address
        if not current_addresses:
            _LOGGER.error("Cannot remove the last Bitcoin address from entry %s", 
                         config_entry_id)
            return
            
        # Update config entry
        new_data = dict(entry.data)
        new_data[CONF_BTC_ADDRESSES] = current_addresses
        hass.config_entries.async_update_entry(entry, data=new_data)
        
        # Reload the entry to apply changes
        await hass.config_entries.async_reload(config_entry_id)
        _LOGGER.info("Removed Bitcoin address %s from entry %s", 
                    btc_address, config_entry_id)
    
    # Register the services
    async_register_admin_service(
        hass,
        DOMAIN,
        "refresh_data",
        refresh_data_service,
    )
    
    async_register_admin_service(
        hass,
        DOMAIN,
        "add_btc_address",
        add_btc_address_service,
        vol.Schema({
            vol.Required("config_entry_id"): cv.string,
            vol.Required("btc_address"): cv.string,
        }),
    )
    
    async_register_admin_service(
        hass,
        DOMAIN,
        "remove_btc_address",
        remove_btc_address_service,
        vol.Schema({
            vol.Required("config_entry_id"): cv.string,
            vol.Required("btc_address"): cv.string,
        }),
    )
    
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Bitcoin Mining from a config entry."""
    host = entry.data[CONF_HOST]
    port = entry.data.get(CONF_PORT, DEFAULT_PORT)
    btc_addresses = entry.data[CONF_BTC_ADDRESSES]
    scan_interval = entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

    session = async_get_clientsession(hass)
    coordinator = BitcoinMiningUpdateCoordinator(
        hass,
        session,
        host,
        port,
        btc_addresses,
        scan_interval,
        entry.entry_id
    )

    await coordinator.async_config_entry_first_refresh()

    if not coordinator.last_update_success:
        raise ConfigEntryNotReady(
            f"Failed to retrieve data from mining server at {host}:{port}"
        )

    hass.data[DOMAIN][entry.entry_id] = coordinator
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    
    return unload_ok

class BitcoinMiningUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Bitcoin Mining data."""

    def __init__(
        self,
        hass: HomeAssistant,
        session: aiohttp.ClientSession,
        host: str,
        port: int,
        btc_addresses: List[str],
        scan_interval: int,
        entry_id: str,
    ) -> None:
        """Initialize."""
        self.session = session
        self.host = host
        self.port = port
        self.btc_addresses = btc_addresses
        self.base_url = f"http://{host}:{port}/api"
        self.entry_id = entry_id
        
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch data from the mining server."""
        data = {
            "client": {},
            "network": {},
            "info": {}
        }
        
        try:
            async with async_timeout.timeout(10):
                # Fetch client data for each BTC address
                for btc_address in self.btc_addresses:
                    client_url = f"{self.base_url}/client/{btc_address}"
                    async with self.session.get(client_url) as resp:
                        if resp.status == 200:
                            client_data = await resp.json()
                            data["client"][btc_address] = client_data
                            
                            # Check for new workers and trigger a reload if needed
                            if self.data and "client" in self.data and btc_address in self.data["client"]:
                                current_workers = set(w["name"] for w in self.data["client"][btc_address].get("workers", []))
                                new_workers = set(w["name"] for w in client_data.get("workers", []))
                                
                                if new_workers - current_workers:
                                    _LOGGER.info(f"New workers detected for {btc_address}: {new_workers - current_workers}")
                                    # Schedule a reload to create entities for new workers
                                    async_dispatcher_send(self.hass, f"{DOMAIN}_new_workers", self.entry_id)
                        else:
                            _LOGGER.error("Failed to fetch client data for %s: %s", 
                                          btc_address, resp.status)
                
                # Fetch network data
                network_url = f"{self.base_url}/network"
                async with self.session.get(network_url) as resp:
                    if resp.status == 200:
                        data["network"] = await resp.json()
                    else:
                        _LOGGER.error("Failed to fetch network data: %s", resp.status)
                
                # Fetch info data
                info_url = f"{self.base_url}/info"
                async with self.session.get(info_url) as resp:
                    if resp.status == 200:
                        data["info"] = await resp.json()
                    else:
                        _LOGGER.error("Failed to fetch info data: %s", resp.status)
                
                return data
                
        except asyncio.TimeoutError:
            raise UpdateFailed(f"Timeout connecting to mining server at {self.host}:{self.port}")
        except (aiohttp.ClientError, ValueError) as error:
            raise UpdateFailed(f"Error fetching data: {error}")
