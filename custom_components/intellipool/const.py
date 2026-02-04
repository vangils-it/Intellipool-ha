"""Constants for IntelliPool integration."""
from __future__ import annotations

from typing import Final

DOMAIN: Final = "intellipool"

# API Configuration
API_BASE_URL: Final = "https://api.domotique-piscine.eu"
API_ENDPOINT: Final = "/api/install/{installation_id}/probes"

# Config keys
CONF_INSTALLATION_ID: Final = "installation_id"
CONF_API_KEY: Final = "api_key"

# Update interval (seconds)
DEFAULT_SCAN_INTERVAL: Final = 60

# Sensor type mappings
SENSOR_TYPES: Final = {
    "WATER_TEMP": {
        "name": "Water Temperature",
        "device_class": "temperature",
        "native_unit": "°C",
        "icon": "mdi:thermometer-water",
        "state_class": "measurement",
    },
    "AIR_TEMP": {
        "name": "Air Temperature",
        "device_class": "temperature",
        "native_unit": "°C",
        "icon": "mdi:thermometer",
        "state_class": "measurement",
    },
    "PH": {
        "name": "pH",
        "device_class": None,
        "native_unit": None,
        "icon": "mdi:ph",
        "state_class": "measurement",
    },
    "ORP": {
        "name": "ORP",
        "device_class": "voltage",
        "native_unit": "mV",
        "icon": "mdi:flash",
        "state_class": "measurement",
    },
    "CONDUCTIVITY": {
        "name": "Conductivity",
        "device_class": None,
        "native_unit": "µS",
        "icon": "mdi:flash-circle",
        "state_class": "measurement",
    },
}

# Binary sensor type mappings
BINARY_SENSOR_TYPES: Final = {
    "OMEOTECH_FLAG_FILTRATION": {
        "name": "Filtration",
        "device_class": "running",
        "icon": "mdi:pump",
    },
    "OMEOTECH_FLAG_HEATING": {
        "name": "Heating",
        "device_class": "heat",
        "icon": "mdi:fire",
    },
    "OMEOTECH_FLAG_LIGHTING": {
        "name": "Lighting",
        "device_class": "light",
        "icon": "mdi:lightbulb",
    },
    "OMEOTECH_FLAG_AUX1": {
        "name": "Auxiliary 1",
        "device_class": "running",
        "icon": "mdi:power",
    },
}
