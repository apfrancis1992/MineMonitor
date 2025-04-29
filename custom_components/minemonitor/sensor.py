"""Sensor platform for MineMonitor integration."""
from __future__ import annotations

import logging
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
    entities = []

    # Add client sensors for each BTC address
    for btc_address in coordinator.btc_addresses:
        if btc_address in coordinator.data["client"]:
            # Add client level sensors
            for description in CLIENT_SENSOR_TYPES:
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
                    for description in WORKER_SENSOR_TYPES:
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

    # Add network sensors
    if coordinator.data["network"]:
        for description in NETWORK_SENSOR_TYPES:
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

    # Add info sensors
    if coordinator.data["info"] and "highScores" in coordinator.data["info"] and coordinator.data["info"]["highScores"]:
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

    async_add_entities(entities)


class MinemonitorSensor(CoordinatorEntity, SensorEntity):
    """Representation of a MineMonitor sensor."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,  # Changed the type hint to generic DataUpdateCoordinator
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
            self._attr_name = f"{btc_address} {description.name}"
        elif sensor_type == "worker" and btc_address and worker_idx is not None:
            worker_name = coordinator.data["client"][btc_address]["workers"][worker_idx]["name"]
            self._attr_unique_id = f"{entry.entry_id}_{btc_address}_{worker_name}_{description.key}"
            self._attr_name = f"{btc_address} {worker_name} {description.name}"
        elif sensor_type == "network":
            self._attr_unique_id = f"{entry.entry_id}_network_{description.key}"
            self._attr_name = f"Bitcoin Network {description.name}"
        elif sensor_type == "info":
            self._attr_unique_id = f"{entry.entry_id}_info_{description.key}"
            self._attr_name = f"MineMonitor {description.name}"

        # Set up the device info
        host = entry.data[CONF_HOST]
        port = entry.data.get(CONF_PORT)
        
        if btc_address:
            self._attr_device_info = DeviceInfo(
                identifiers={(DOMAIN, f"{host}:{port}_{btc_address}")},
                name=f"MineMonitor {btc_address}",
                manufacturer="Alex Francis",
                model="Mining Monitor",
                configuration_url=f"http://{host}:{port}/api/client/{btc_address}",
            )
        else:
            self._attr_device_info = DeviceInfo(
                identifiers={(DOMAIN, f"{host}:{port}")},
                name="MineMonitor Network",
                manufacturer="Alex Francis",
                model="Mining Monitor",
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
