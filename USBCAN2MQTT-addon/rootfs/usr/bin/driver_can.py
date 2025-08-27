#!/usr/bin/env python3
import json
import logging
import os
import time
from gs_usb.gs_usb import GsUsb, GS_CAN_MODE_NORMAL
from gs_usb.gs_usb_frame import GsUsbFrame
from gs_usb.constants import CAN_EFF_FLAG
import paho.mqtt.client as mqtt
from threading import Thread
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s :: [%(filename)12s:%(lineno)-4d] :: %(levelname)-8s :: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)
# Load environment variables from .env file if it exists (for local debugging)


def load_env_file():
    """Charge les variables d'environnement depuis un fichier .env pour le débogage local."""
    env_file = os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env')
    to_return = {}
    if os.path.exists(env_file):
        logger.info(f"Loading environment variables from {env_file}")
        try:
            with open(env_file, 'r') as f:
                for line in f:
                    try:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            to_return[key] = value
                    except Exception as e:
                        logger.error(f"erreur sur la ligne {line} : {e}")
        except Exception as e:
            logger.error(f"Erreur lors du chargement du fichier .env: {e}")
    else:
        logger.info("Fichier .env non trouvé, utilisation des variables d'environnement du système")
    return to_return


def load_config():
    """Charge la configuration depuis options.json."""
    try:
        with open("/data/options.json", "r") as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Erreur de chargement : {e}")
        return load_env_file()


def save_config(config):
    """Sauvegarde la configuration dans options.json."""
    try:
        with open("/data/options.json", "w") as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        logger.error(f"Erreur de sauvegarde : {e}")


config = load_config()
logger.info(config)


# MQTT Broker configuration from environment variables
MQTT_BROKER = config.get('MQTT_HOST', 'localhost')

MQTT_PORT = config.get('MQTT_PORT', '1883')
if MQTT_PORT is None or MQTT_PORT == "" or MQTT_PORT == "None" or MQTT_PORT == "null" or MQTT_PORT == "Null" or MQTT_PORT == "NULL":
    MQTT_PORT = 1883
else:
    MQTT_PORT = int(MQTT_PORT)

MQTT_USERNAME = config.get('MQTT_USER', 'mqtt')
MQTT_PASSWORD = config.get('MQTT_PASSWORD', 'mqtt')
MQTT_RX_TOPIC = config.get('MQTT_RX_TOPIC', 'can/rx')
MQTT_TX_TOPIC = config.get('MQTT_TX_TOPIC', 'can/tx')

logger.info(f"MQTT_BROKER : {MQTT_BROKER}")
logger.info(f"MQTT_PORT : {MQTT_PORT}")
logger.info(f"MQTT_USERNAME : {MQTT_USERNAME}")
logger.info(f"MQTT_PASSWORD : {MQTT_PASSWORD}")
logger.info(f"MQTT_RX_TOPIC : {MQTT_RX_TOPIC}")
logger.info(f"MQTT_TX_TOPIC : {MQTT_TX_TOPIC}")

# Configuration
BITRATE = 250000

# Initialize MQTT client
client = mqtt.Client()


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info("Connected to MQTT broker successfully")
        # Subscribe to MQTT topic for transmitting messages
        client.subscribe(MQTT_TX_TOPIC)
        logger.info(f"Subscribed to MQTT topic {MQTT_TX_TOPIC}")
    else:
        logger.error(f"Failed to connect to MQTT broker, return code {rc}")


def on_message(client, userdata, msg):
    try:
        logger.info(f"Received message on topic {msg.topic}")
        if msg.topic == MQTT_TX_TOPIC:
            # Decode message payload
            payload = json.loads(msg.payload.decode('utf-8'))
            can_id = int(payload['id'], 16)
            data = bytes.fromhex(payload['data'])

            # Construct and send CAN frame
            can_frame = GsUsbFrame(can_id=can_id | CAN_EFF_FLAG, data=data)
            if dev.send(can_frame):
                logger.info(f"Sent: {can_frame}")
            else:
                logger.error(f"Failed to send CAN frame {can_frame}")
    except Exception as e:
        logger.error(f"Error processing MQTT message - {e}")


client.on_connect = on_connect
client.on_message = on_message

while True:
    try:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.reconnect_delay_set(min_delay=1, max_delay=5)
        Thread(target=client.loop_forever, args=(1, True)).start()
        logger.info(f"Connecting to MQTT broker at {MQTT_BROKER}:{MQTT_PORT} as {MQTT_USERNAME}")
        break
    except Exception as e:
        logger.error(f"Error connecting to MQTT broker: {e}")
        time.sleep(1)


# Function to publish CAN message to MQTT
def publish_can_message(can_msg):
    can_data = {"id": f"{can_msg.arbitration_id:08x}", "data": "".join("{:02X}".format(b) for b in can_msg.data[:can_msg.can_dlc]), "rtr": can_msg.is_remote_frame}
    mqtt_msg = json.dumps(can_data)
    client.publish(MQTT_RX_TOPIC, mqtt_msg)
    logger.debug(f"Published: {can_msg}")


# Initialize the USB-to-CAN device
dev = None
while True:
    try:
        devs = GsUsb.scan()
        if len(devs) == 0:
            logger.info("Cannot find gs_usb device")
            time.sleep(1)
            continue

        dev = devs[0]

        # Configuration
        if not dev.set_bitrate(BITRATE):
            logger.error("Cannot set bitrate for gs_usb")
            exit(1)

        # Start device
        dev.start(GS_CAN_MODE_NORMAL)
        logger.info("Started gs_usb device in normal mode")
        break
    except Exception as e:
        logger.error(f"Error while starting device - {e}")
        time.sleep(1)

# Read all the time and send a message each second

try:
    while True:
        iframe = GsUsbFrame()
        if dev.read(iframe, 1):
            publish_can_message(iframe)
except KeyboardInterrupt:
    logger.info("Script interrupted by user")
finally:
    dev.stop()
    client.loop_stop()
    client.disconnect()
