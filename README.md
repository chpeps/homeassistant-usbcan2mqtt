# USBCAN2MQTT Home Assistant Add-on

[![Build & Test](https://github.com/chpeps/homeassistant-usbcan2mqtt/actions/workflows/build.yml/badge.svg)](https://github.com/chpeps/homeassistant-usbcan2mqtt/actions/workflows/build.yml)
![Archs](https://img.shields.io/badge/platform-arm%2Carm64%2Camd64%2Ci386-green.svg)

---

## Overview
This Home Assistant add-on publishes CAN frames from a USB-CAN adapter to MQTT, and can inject MQTT messages back onto the CAN bus. It is designed for marine, automation, and IoT environments where CAN <-> MQTT bridging is useful.

**Main features:**
- Supports GS-USB adapters (Linux only)
- Bidirectional CAN <-> MQTT bridge
- Home Assistant-friendly configuration (YAML/JSON)
- Publishes received CAN frames on `can/rx` MQTT topic, subscribes to `can/tx`
- Secure MQTT credentials management
- Multi-platform (armhf, armv7, aarch64, amd64, i386)

**Note:** All add-on files (Dockerfile, config.yaml, etc.) are now located at the root of this repository. Add this repository directly as a custom add-on source in Home Assistant.

---

## Installation in Home Assistant

[![Open your Home Assistant instance and show the add add-on repository dialog with a specific repository URL pre-filled.](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fchpeps%2Fhomeassistant-usbcan2mqtt)

1. Make sure your MQTT broker (e.g., Mosquitto) is running and accessible. (Install via Supervisor if needed.)
2. In Home Assistant, go to **Settings > Add-ons > Add-on Store > 3-dot menu > Repositories**.
3. Paste the repository URL:
   ```
   https://github.com/chpeps/homeassistant-usbcan2mqtt
   ```
   and click "Add".
4. You should now see USBCAN2MQTT listed as an available add-on. Click to install.
5. Configure MQTT access and topics (see below).
6. Start the add-on. Check its logs for any errors.

---

## Configuration & Usage

**Minimal configuration (in the add-on UI or in `config.yaml`):**
```yaml
MQTT_HOST: 192.168.1.20
MQTT_PORT: 1883
MQTT_USER: youruser  # Required
MQTT_PASSWORD: yourpassword  # Required
MQTT_RX_TOPIC: can/rx
MQTT_TX_TOPIC: can/tx
```
> By default, you must set MQTT credentials. The values above are just examples.

### Example: Home Assistant `configuration.yaml`
```yaml
mqtt:
  broker: 192.168.1.20
  username: youruser
  password: yourpassword

sensor:
  - platform: mqtt
    name: "CAN Battery Voltage"
    state_topic: "can/rx"
    value_template: "{{ value_json.data }}"
```

## MQTT Topics & JSON Payload
- `can/rx`: receives all CAN messages from USB, published as JSON by the add-on
- `can/tx`: you can send messages here (in the below format) to be written on the bus

**Payload format:**
```json
{
  "id": "0CF00401",
  "data": "FF0000AABE...",
  "rtr": false
}
```
---

## Supported Architectures
- aarch64, amd64, armhf, armv7, i386

## License
MIT (c) 2025 Chpeps

---
## Additional Notes
- All add-on files are now at the repository root (not under /addon). Any older doc or config referring to `/addon/` paths is obsolete.
- For questions or support, visit the [GitHub Discussions](https://github.com/chpeps/homeassistant-usbcan2mqtt/discussions).
- See also the Dockerfile and config.yaml at the root for contributor/maintainer options.
