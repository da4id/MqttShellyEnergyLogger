import json
import logging.config
import os
import time
from datetime import datetime
import sys
import signal
from ShellyMqttMsgHandler import ShellyMqttMsgHandler
import paho.mqtt.client as mqtt

ID = "ShellyAdapter" + str(datetime.now())

def setup_logging(
        default_path=os.path.dirname(os.path.abspath(__file__)) + '/logging.json',
        default_level=logging.INFO,
        env_key='LOG_CFG'
):
    """Setup logging configuration

    """
    path = default_path
    value = os.getenv(env_key, None)
    if value:
        path = value
    if os.path.exists(path):
        with open(path, 'rt') as f:
            config = json.load(f)
        logging.config.dictConfig(config)
    else:
        print("use default config, no config file found")
        logging.basicConfig(level=default_level)

def signal_term(signal, frame):
    shellyMqttMsgHandler.loop_stop(True)
    shellyMqttMsgHandler.stopTimer = True
    logging.shutdown()
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGTERM, signal_term)
    signal.signal(signal.SIGINT, signal_term)
    setup_logging()

    Server = os.environ.get('MQTT_SERVER')
    Port = int(os.environ.get('MQTT_PORT'))
    User = os.environ.get('MQTT_USER')
    Password = os.environ.get('MQTT_PASSWORD')

    shellyMqttMsgHandler = ShellyMqttMsgHandler(mqtt.CallbackAPIVersion.VERSION2, ID, clean_session=True)
    shellyMqttMsgHandler.run(User, Password, Server, Port)


    while (True):
        time.sleep(3600)
