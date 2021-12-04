"""
volumio-to-mqtt - a utility for properly controlling/observing volumio via mqtt
Copyright (C) 2021 Stichting De Jonge Onderzoekers Amersfoort

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
"""

import paho.mqtt.client as mqtt
import requests
import json
import configparser
import logging
import time

def messageHandler(mqttc, obj, msg):
    
    
    pl = msg.payload.decode()
    if msg.topic == config['MQTT_envelopes']['prefix'] + 'set_volume':
        logging.debug("Received volume message")
        try:
            volume = int(pl)
            #assert pl <= 100 and pl >= 0
        except:
            logging.error("Invalid volume message")
            return
        if volume != current_state['volume']:
            logging.debug("Changing volume to {}".format(volume))
            requests.get("{}{}?cmd=volume&volume={}".format(config['volumio']['host'], config['volumio']['command_endpoint'], volume))
        
    if msg.topic == config['MQTT_envelopes']['prefix'] + 'set_status':
        logging.debug("Received status message")
        # There's no need to send a new status message, that will be done automatically on the next loop
        if pl == "toggle":
            logging.debug("Toggling player")
            requests.get("{}{}?cmd=toggle".format(config['volumio']['host'], config['volumio']['command_endpoint']))
        elif pl == "pause":
            logging.debug("Pausing player")
            requests.get("{}{}?cmd=pause".format(config['volumio']['host'], config['volumio']['command_endpoint']))
        elif pl == "play":
            logging.debug("Resuming player")
            requests.get("{}{}?cmd=play".format(config['volumio']['host'], config['volumio']['command_endpoint']))
        else:
            logging.error("Invalid value for status: {}".format(pl))


def compareResponseAndState(name, new_value):
    if current_state[name] != new_value:
        envelope = config['MQTT_envelopes']['prefix'] + config['MQTT_envelopes'][name]
        logging.debug("{} changed, will send '{}' to {}".format(name, new_value, envelope))
        mqtt_client.publish(envelope, payload=new_value, retain=True)
        current_state[name] = new_value
    else:
        logging.debug("{} not changed (value: {})".format(name, new_value))

global config
config = configparser.ConfigParser()
config.read('config.ini')

logging.basicConfig(level=config['logging']['channel'])

global mqtt_client
mqtt_client = mqtt.Client(config['MQTT_connection']['name'])
if(bool(config['MQTT_connection']['password_needed'])):
    # Password is required according to config, supply credentials
    logging.info("Using provided username and password")
    mqtt_client.username_pw_set(username=config['MQTT_connection']['username'], password=config['MQTT_connection']['password'])


logging.info("Connecting to MQTT broker @ {} (port {})".format(config['MQTT_connection']['mqtt_host'], config['MQTT_connection']['mqtt_port']))
mqtt_client.connect(config['MQTT_connection']['mqtt_host'], int(config['MQTT_connection']['mqtt_port']))

mqtt_subscription_filter = config['MQTT_envelopes']['prefix'] + "#"
logging.debug("Subscribing to {}".format(mqtt_subscription_filter))

mqtt_client.subscribe(mqtt_subscription_filter, 0)
mqtt_client.on_message = messageHandler

mqtt_client.loop_start()

logging.info("Starting main loop")

global current_state
current_state = {'status': False, 'title': False, 'artist': False, 'album': False, 'volume': False, 'seek': False, 'duration': False, 'service': False, 'stream': False, 'mute': False, 'uri': False, 'albumart': False, 'position': False}


while True:
    logging.debug("Sleeping for {} milliseconds".format(config['volumio']['interval']))
    time.sleep(int(config['volumio']['interval']) / 1000)
    logging.debug("Current state: {}".format(str(current_state)))
    
    try:
        r = requests.get(config['volumio']['host'] + config['volumio']['get_state_endpoint'])
    except:
        logging.error("Failed to get volumio state")
    if r.status_code != 200:
        logging.error("Request for volumio state didn't return HTTP 200")
        
    
    try:
        responsedata = r.json()
    except json.decoder.JSONDecodeError:
        logging.error("Failed to decode response from volumio as JSON")

    compareResponseAndState('status', getattr(responsedata, 'status', ''))
    compareResponseAndState('title', getattr(responsedata, 'title', ''))
    compareResponseAndState('artist', getattr(responsedata, 'artist', ''))
    compareResponseAndState('album', getattr(responsedata, 'album', ''))
    compareResponseAndState('volume', getattr(responsedata, 'volume', 0))
    compareResponseAndState('seek', getattr(responsedata, 'seek', 0))
    compareResponseAndState('duration', getattr(responsedata, 'duration', 0))
    compareResponseAndState('service', getattr(responsedata, 'service', ''))
    compareResponseAndState('stream', getattr(responsedata, 'stream', ''))
    compareResponseAndState('mute', getattr(responsedata, 'mute', False))
    compareResponseAndState('uri', getattr(responsedata, 'uri', ''))
    compareResponseAndState('albumart', getattr(responsedata, 'albumart', ''))
    compareResponseAndState('position', getattr(responsedata, 'position', 0))