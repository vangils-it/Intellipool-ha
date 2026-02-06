# IntelliPool Home Assistant Integration

A custom Home Assistant integration for Pentair IntelliPool pool automation systems.

## Features

### Sensors (Read-only)
- Water Temperature
- Air Temperature
- pH Level
- ORP (Redox)
- Conductivity

### Binary Sensors (Read-only)
- Filtration Status
- Heating Status

### Switches (Controllable - requires Session Token)
- Lighting
- Auxiliary 1

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
   - **Session Token**: (Optional) Required for control features
   - **Pool Name**: A friendly name for your pool (optional)

## Finding Your Credentials

You can find your Installation ID and API Key in the IntelliPool mobile app or by contacting your pool installer.

### Session Token (for control features)

The session token is required to control your pool equipment (lights, etc.). You can obtain it by:
1. Using a network proxy (like mitmproxy) to capture traffic from the IntelliPool app
2. Look for the `sessionToken` field in the WebSocket messages

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
| `switch.intellipool_lighting` | Switch | Pool lights (on/off) |
| `switch.intellipool_auxiliary_1` | Switch | Auxiliary output 1 |

## Update Interval

The integration polls the IntelliPool API every 60 seconds by default.

## Known Limitations

- Control features require a valid session token
- Session tokens may expire and need to be refreshed
- Requires an active internet connection to the IntelliPool cloud

## Troubleshooting

### "Invalid API key or installation ID"
- Double-check your credentials
- Ensure your IntelliPool subscription is active

### "Failed to connect"
- Check your internet connection
- The IntelliPool API may be temporarily unavailable

### Switches not appearing
- Make sure you provided a valid session token
- Check the Home Assistant logs for WebSocket connection errors

## Changelog

### v1.1.0
- Added WebSocket support for control features
- Added switches for lighting and auxiliary 1
- Added session token configuration option

### v1.0.0
- Initial release
- Read-only sensors and binary sensors

## Credits

- Developed for Home Assistant
- IntelliPool is a product of Pentair

## License

MIT License
