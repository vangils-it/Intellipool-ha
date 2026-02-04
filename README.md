# IntelliPool Home Assistant Integration

A custom Home Assistant integration for Pentair IntelliPool pool automation systems.

## Features

- **Sensors:**
  - Water Temperature
  - Air Temperature
  - pH Level
  - ORP (Redox)
  - Conductivity

- **Binary Sensors:**
  - Filtration Status
  - Heating Status
  - Lighting Status
  - Auxiliary 1 Status

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click on "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL and select "Integration" as the category
6. Click "Install"
7. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/intellipool` folder to your Home Assistant `custom_components` directory
2. Restart Home Assistant

## Configuration

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "IntelliPool"
4. Enter your credentials:
   - **Installation ID**: Your IntelliPool installation ID
   - **API Key**: Your IntelliPool API key
   - **Pool Name**: A friendly name for your pool (optional)

## Finding Your Credentials

You can find your Installation ID and API Key in the IntelliPool mobile app or by contacting your pool installer.

## Entities Created

After setup, the following entities will be created:

| Entity | Type | Description |
|--------|------|-------------|
| `sensor.intellipool_water_temperature` | Sensor | Current water temperature |
| `sensor.intellipool_air_temperature` | Sensor | Current air temperature |
| `sensor.intellipool_ph` | Sensor | Current pH level |
| `sensor.intellipool_orp` | Sensor | ORP/Redox value in mV |
| `sensor.intellipool_conductivity` | Sensor | Conductivity in µS |
| `binary_sensor.intellipool_filtration` | Binary Sensor | Filtration pump status |
| `binary_sensor.intellipool_heating` | Binary Sensor | Heater status |
| `binary_sensor.intellipool_lighting` | Binary Sensor | Pool lights status |
| `binary_sensor.intellipool_auxiliary_1` | Binary Sensor | Auxiliary output 1 status |

## Update Interval

The integration polls the IntelliPool API every 60 seconds by default.

## Known Limitations

- This is a **read-only** integration - you cannot control the pool equipment from Home Assistant (yet)
- Requires an active internet connection to the IntelliPool cloud

## Troubleshooting

### "Invalid API key or installation ID"
- Double-check your credentials
- Ensure your IntelliPool subscription is active

### "Failed to connect"
- Check your internet connection
- The IntelliPool API may be temporarily unavailable

## Credits

- Developed for Home Assistant
- IntelliPool is a product of Pentair

## License

MIT License
