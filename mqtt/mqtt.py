from fileinput import close
from platform import release
from numpy import isin
import paho.mqtt.client as mqtt
import websocket
import json
import rel

# check if key is an array index
def has_arr(arr, index):
    if not isinstance(arr, list): return False
    if not isinstance(index, int): return False
    if index < 0 or index >= len(arr): return False
    return True

# parse a key from the provided object or return None
def get_key(obj, *keys):
    for key in keys:
        # check if either key exists or is array index
        if key in obj or has_arr(obj, key):
            obj = obj[key]
        else:
            return None
    
    return obj

# config class
class Config:
    def __init__(self):
        self.ws_host = 'ws://100.64.0.157/mopidy/ws'
        self.mqtt_host = 'mqtt.bitlair.nl'
        self.mqtt_port = 1883
        self.mqtt_name = 'DJO_Mopidy_to_MQTT'

# class for the MQTT proxy client
class Proxy:
    def __init__(self, config:Config):
        self.config = config
        self.state = {
            'status': 'paused',
            'title': 'tietel',
            'artist': 'artietst',
            'album': 'albuuum',
            'volume': 0,
            'seek': 0,
            'duration': 0
        }

        # websocket.enableTrace(True)
        self.mqtt_client = mqtt.Client(self.config.mqtt_name)
        self.ws_client = websocket.WebSocketApp(self.config.ws_host, on_message=self.on_message)

    # connect to the client
    def connect(self):
        self.mqtt_client.connect(self.config.mqtt_host, self.config.mqtt_port)

        self.ws_client.run_forever(dispatcher=rel)
        rel.signal(2, rel.abort)
        rel.dispatch()

    def publish(self, key, value):
        if self.state[key] != value and value is not None:
            envelope = self.config.mqtt_name + '/' + key
            print("{} changed, will send '{}' to {}".format(key, value, envelope))
            self.mqtt_client.publish(envelope, payload=value, retain=True)
            self.state[key] = value

    def on_message(self, ws, message):
        data = json.loads(message)

        self.publish('volume',      get_key(data, 'volume'))
        self.publish('seek',        get_key(data, 'time_position'))
        self.publish('status',      get_key(data, 'new_state'))
        self.publish('title',       get_key(data, 'tl_track', 'track', 'name'))
        self.publish('duration',    get_key(data, 'tl_track', 'track', 'length'))
        self.publish('album',       get_key(data, 'tl_track', 'track', 'album', 'name'))
        self.publish('artist',      get_key(data, 'tl_track', 'track', 'artists', 0, 'name'))

if __name__ == '__main__':
    config = Config()
    proxy = Proxy(config)
    proxy.connect()