"""Sensor platform for MineMonitor integration."""
from __future__ import annotations

import logging
import itertools
from typing import Any, Dict, Optional, List, cast

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from . import DOMAIN  # Import just the DOMAIN constant

_LOGGER = logging.getLogger(__name__)

def convert_to_th_per_second(hashrate):
    """Convert hashrate from H/s to TH/s."""
    if hashrate is None:
        return None
    # Convert from H/s to TH/s (1 TH/s = 1,000,000,000,000 H/s)
    # Format to 2 decimal places
    return round(float(hashrate) / 1_000_000_000_000, 2)

def format_difficulty(difficulty):
    """Format difficulty value with no decimals."""
    if difficulty is None:
        return None
    try:
        # Convert to integer by rounding
        return round(float(difficulty))
    except (ValueError, TypeError):
        return difficulty

# Sensor types for client data
CLIENT_SENSOR_TYPES: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="bestDifficulty",
        name="Best Difficulty",
        icon="mdi:pickaxe",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="workersCount",
        name="Workers Count",
        icon="mdi:account-group",
        state_class=SensorStateClass.MEASUREMENT,
    ),
)

# Total hashrate sensor
TOTAL_HASHRATE_SENSOR = SensorEntityDescription(
    key="totalHashRate",
    name="Total Hash Rate",
    icon="mdi:lightning-bolt",
    native_unit_of_measurement="TH/s",
    state_class=SensorStateClass.MEASUREMENT,
)

# Sensor types for worker data
WORKER_SENSOR_TYPES: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="bestDifficulty",
        name="Best Difficulty",
        icon="mdi:pickaxe",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="hashRate",
        name="Hash Rate",
        icon="mdi:chip",
        native_unit_of_measurement="TH/s",  # Changed from H/s to TH/s
        state_class=SensorStateClass.MEASUREMENT,
    ),
)

# Sensor types for network data
NETWORK_SENSOR_TYPES: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="blocks",
        name="Blocks",
        icon="mdi:cube-outline",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="difficulty",
        name="Network Difficulty",
        icon="mdi:chart-line",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="networkhashps",
        name="Network Hash Rate",
        icon="mdi:server-network",
        native_unit_of_measurement="TH/s",  # Changed from H/s to TH/s
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="pooledtx",
        name="Pooled Transactions",
        icon="mdi:ballot",
        state_class=SensorStateClass.MEASUREMENT,
    ),
)

# Sensor types for info data
INFO_SENSOR_TYPES: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="highscore_bestDifficulty",
        name="All-time Best Difficulty",
        icon="mdi:trophy",
        state_class=SensorStateClass.MEASUREMENT,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up MineMonitor sensors based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    # Create a set to track existing worker names
    worker_tracker = set()
    
    def setup_sensors():
        """Set up sensors from coordinator data."""
        entities = []
        
        # Add client sensors for each BTC address
        for btc_address in coordinator.btc_addresses:
            if btc_address in coordinator.data["client"]:
                # Add client level sensors (skipping if they already exist)
                for description in CLIENT_SENSOR_TYPES:
                    entity_id = f"{entry.entry_id}_{btc_address}_{description.key}"
                    if entity_id not in worker_tracker:
                        worker_tracker.add(entity_id)
                        entities.append(
                            MinemonitorSensor(
                                coordinator,
                                description,
                                entry,
                                btc_address,
                                "client",
                                None,
                            )
                        )
                
                # Add worker level sensors
                if "workers" in coordinator.data["client"][btc_address]:
                    for worker_idx, worker in enumerate(coordinator.data["client"][btc_address]["workers"]):
                        worker_name = worker.get("name", f"worker_{worker_idx}")
                        for description in WORKER_SENSOR_TYPES:
                            entity_id = f"{entry.entry_id}_{btc_address}_{worker_name}_{description.key}"
                            if entity_id not in worker_tracker:
                                worker_tracker.add(entity_id)
                                entities.append(
                                    MinemonitorSensor(
                                        coordinator,
                                        description,
                                        entry,
                                        btc_address,
                                        "worker",
                                        worker_idx,
                                    )
                                )
        
        # Add network sensors (skipping if they already exist)
        if coordinator.data["network"]:
            for description in NETWORK_SENSOR_TYPES:
                entity_id = f"{entry.entry_id}_network_{description.key}"
                if entity_id not in worker_tracker:
                    worker_tracker.add(entity_id)
                    entities.append(
                        MinemonitorSensor(
                            coordinator,
                            description,
                            entry,
                            None,
                            "network",
                            None,
                        )
                    )
        
        # Add info sensors (skipping if they already exist)
        if coordinator.data["info"] and "highScores" in coordinator.data["info"] and coordinator.data["info"]["highScores"]:
            entity_id = f"{entry.entry_id}_info_highscore_bestDifficulty"
            if entity_id not in worker_tracker:
                worker_tracker.add(entity_id)
                entities.append(
                    MinemonitorSensor(
                        coordinator,
                        INFO_SENSOR_TYPES[0],  # High score difficulty
                        entry,
                        None,
                        "info",
                        None,
                    )
                )
        
        # Add total hashrate sensor (skipping if it already exists)
        entity_id = f"{entry.entry_id}_total_hashrate"
        if entity_id not in worker_tracker:
            worker_tracker.add(entity_id)
            entities.append(
                TotalHashrateSensor(
                    coordinator,
                    TOTAL_HASHRATE_SENSOR,
                    entry,
                )
            )
        
        if entities:
            async_add_entities(entities)
    
    # Set up initial entities
    setup_sensors()
    
    # Register to handle new worker signals
    async def handle_new_workers(entry_id):
        if entry_id == entry.entry_id:
            setup_sensors()
    
    # Listen for the signal
    async_dispatcher_connect(hass, f"{DOMAIN}_new_workers", handle_new_workers)


class MinemonitorSensor(CoordinatorEntity, SensorEntity):
    """Representation of a MineMonitor sensor."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        description: SensorEntityDescription,
        entry: ConfigEntry,
        btc_address: Optional[str],
        sensor_type: str,
        worker_idx: Optional[int],
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._entry = entry
        self._btc_address = btc_address
        self._sensor_type = sensor_type
        self._worker_idx = worker_idx
        
        # Set unique_id based on sensor type
        if sensor_type == "client" and btc_address:
            self._attr_unique_id = f"{entry.entry_id}_{btc_address}_{description.key}"
            self._attr_name = f"{btc_address[:6]}... {description.name}"
        elif sensor_type == "worker" and btc_address and worker_idx is not None:
            worker_data = coordinator.data["client"][btc_address]["workers"][worker_idx]
            worker_name = worker_data.get("name", f"worker_{worker_idx}")
            self._attr_unique_id = f"{entry.entry_id}_{btc_address}_{worker_name}_{description.key}"
            self._attr_name = f"{worker_name} {description.name}"
        elif sensor_type == "network":
            self._attr_unique_id = f"{entry.entry_id}_network_{description.key}"
            self._attr_name = f"Bitcoin Network {description.name}"
        elif sensor_type == "info":
            self._attr_unique_id = f"{entry.entry_id}_info_{description.key}"
            self._attr_name = f"MineMonitor {description.name}"

        # Set up the device info with improved names
        host = entry.data[CONF_HOST]
        port = entry.data.get(CONF_PORT)
        
        if sensor_type == "worker" and btc_address and worker_idx is not None:
            worker_data = coordinator.data["client"][btc_address]["workers"][worker_idx]
            worker_name = worker_data.get("name", f"worker_{worker_idx}")
            
            # Use worker name for the device
            self._attr_device_info = DeviceInfo(
                identifiers={(DOMAIN, f"{host}:{port}_{btc_address}_{worker_name}")},
                name=f"Worker {worker_name}",
                manufacturer="MineMonitor",
                model="Mining Worker",
                via_device=(DOMAIN, f"{host}:{port}"),
                configuration_url=f"http://{host}:{port}/api/client/{btc_address}",
            )
        elif sensor_type == "client" and btc_address:
            # Use a shortened BTC address for client device
            short_address = f"{btc_address[:6]}...{btc_address[-6:]}"
            self._attr_device_info = DeviceInfo(
                identifiers={(DOMAIN, f"{host}:{port}_{btc_address}")},
                name=f"Mining Address {short_address}",
                manufacturer="MineMonitor",
                model="Mining Address",
                via_device=(DOMAIN, f"{host}:{port}"),
                configuration_url=f"http://{host}:{port}/api/client/{btc_address}",
            )
        else:
            # Network device
            self._attr_device_info = DeviceInfo(
                identifiers={(DOMAIN, f"{host}:{port}")},
                name="MineMonitor Network",
                manufacturer="MineMonitor",
                model="Mining Server",
                configuration_url=f"http://{host}:{port}/api",
            )

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None

        if self._sensor_type == "client" and self._btc_address:
            # Return client-level data
            client_data = self.coordinator.data["client"].get(self._btc_address, {})
            value = client_data.get(self.entity_description.key)
            # Format difficulty with no decimals
            if self.entity_description.key == "bestDifficulty":
                return format_difficulty(value)
            return value
            
        elif self._sensor_type == "worker" and self._btc_address and self._worker_idx is not None:
            # Return worker-level data
            client_data = self.coordinator.data["client"].get(self._btc_address, {})
            workers = client_data.get("workers", [])
            
            if 0 <= self._worker_idx < len(workers):
                worker_data = workers[self._worker_idx]
                # Get the value
                value = worker_data.get(self.entity_description.key)
                
                # Format difficulty with no decimals
                if self.entity_description.key == "bestDifficulty":
                    return format_difficulty(value)
                # Convert hashrates from H/s to TH/s with 2 decimal places
                elif self.entity_description.key == "hashRate":
                    try:
                        return convert_to_th_per_second(float(value))
                    except (ValueError, TypeError):
                        return value
                return value
            return None
            
        elif self._sensor_type == "network":
            # Return network data
            network_data = self.coordinator.data.get("network", {})
            
            # Format difficulty with no decimals
            if self.entity_description.key == "difficulty":
                return format_difficulty(network_data.get(self.entity_description.key))
            # Convert networkhashps from H/s to TH/s with 2 decimal places
            elif self.entity_description.key == "networkhashps":
                try:
                    value = network_data.get(self.entity_description.key)
                    return convert_to_th_per_second(float(value))
                except (ValueError, TypeError):
                    return network_data.get(self.entity_description.key)
            
            return network_data.get(self.entity_description.key)
            
        elif self._sensor_type == "info" and self.entity_description.key == "highscore_bestDifficulty":
            # Return high score data with formatted difficulty
            info_data = self.coordinator.data.get("info", {})
            high_scores = info_data.get("highScores", [])
            if high_scores:
                return format_difficulty(high_scores[0].get("bestDifficulty"))
            
        return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        if not self.coordinator.last_update_success:
            return False
            
        if self._sensor_type == "client" and self._btc_address:
            return self._btc_address in self.coordinator.data.get("client", {})
        elif self._sensor_type == "worker" and self._btc_address and self._worker_idx is not None:
            client_data = self.coordinator.data.get("client", {}).get(self._btc_address, {})
            workers = client_data.get("workers", [])
            return 0 <= self._worker_idx < len(workers)
        elif self._sensor_type == "network":
            return bool(self.coordinator.data.get("network"))
        elif self._sensor_type == "info":
            info_data = self.coordinator.data.get("info", {})
            return bool(info_data.get("highScores"))
            
        return False

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return additional state attributes for the sensor."""
        attributes = {}
        
        if self._sensor_type == "worker" and self._btc_address and self._worker_idx is not None:
            # Add worker attributes
            client_data = self.coordinator.data["client"].get(self._btc_address, {})
            workers = client_data.get("workers", [])
            
            if 0 <= self._worker_idx < len(workers):
                worker_data = workers[self._worker_idx]
                
                # Add all available worker attributes
                for key, value in worker_data.items():
                    if key != self.entity_description.key:  # Don't duplicate the state value
                        attributes[key] = value
                
                # Add BTC address to the attributes
                attributes["btc_address"] = self._btc_address
        
        return attributes


class TotalHashrateSensor(CoordinatorEntity, SensorEntity):
    """Sensor for total hashrate across all workers."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        description: SensorEntityDescription,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the total hashrate sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._entry = entry
        
        # Set unique_id
        self._attr_unique_id = f"{entry.entry_id}_total_hashrate"
        self._attr_name = "Total Mining Hashrate"
        
        # Set up device info
        host = entry.data[CONF_HOST]
        port = entry.data.get(CONF_PORT)
        
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{host}:{port}")},
            name="MineMonitor Network",
            manufacturer="MineMonitor",
            model="Mining Server",
            configuration_url=f"http://{host}:{port}/api",
        )

    @property
    def native_value(self) -> StateType:
        """Return the total hashrate across all workers."""
        if not self.coordinator.data:
            return None
        
        total_hashrate = 0.0
        
        # Sum up hashrates from all workers across all BTC addresses
        for btc_address in self.coordinator.btc_addresses:
            if btc_address in self.coordinator.data["client"]:
                client_data = self.coordinator.data["client"][btc_address]
                workers = client_data.get("workers", [])
                
                for worker in workers:
                    try:
                        worker_hashrate = float(worker.get("hashRate", 0))
                        total_hashrate += worker_hashrate
                    except (ValueError, TypeError):
                        pass
        
        # Convert from H/s to TH/s
        return convert_to_th_per_second(total_hashrate)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        if not self.coordinator.last_update_success:
            return False
            
        # Check if we have any valid client data
        for btc_address in self.coordinator.btc_addresses:
            if btc_address in self.coordinator.data.get("client", {}):
                return True
                
        return False

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return additional attributes about the total hashrate."""
        attributes = {}
        
        # Count active workers
        active_workers = 0
        total_workers = 0
        
        # Sum up workers from all BTC addresses
        for btc_address in self.coordinator.btc_addresses:
            if btc_address in self.coordinator.data.get("client", {}):
                client_data = self.coordinator.data["client"][btc_address]
                workers = client_data.get("workers", [])
                
                total_workers += len(workers)
                
                for worker in workers:
                    # Consider a worker active if it has a non-zero hashrate
                    try:
                        worker_hashrate = float(worker.get("hashRate", 0))
                        if worker_hashrate > 0:
                            active_workers += 1
                    except (ValueError, TypeError):
                        pass
        
        attributes["active_workers"] = active_workers
        attributes["total_workers"] = total_workers
        
        # Calculate network share if network hashrate is available
        if "network" in self.coordinator.data and "networkhashps" in self.coordinator.data["network"]:
            try:
                network_hashrate = float(self.coordinator.data["network"]["networkhashps"])
                if network_hashrate > 0:
                    # Calculate percentage share (total_hashrate / network_hashrate) * 100
                    total_hashrate_raw = 0.0
                    for btc_address in self.coordinator.btc_addresses:
                        if btc_address in self.coordinator.data.get("client", {}):
                            client_data = self.coordinator.data["client"][btc_address]
                            workers = client_data.get("workers", [])
                            
                            for worker in workers:
                                try:
                                    worker_hashrate = float(worker.get("hashRate", 0))
                                    total_hashrate_raw += worker_hashrate
                                except (ValueError, TypeError):
                                    pass
                    
                    network_share = (total_hashrate_raw / network_hashrate) * 100
                    attributes["network_share"] = round(network_share, 6)  # Percentage with 6 decimal places
            except (ValueError, TypeError, ZeroDivisionError):
                pass
        
        return attributes
