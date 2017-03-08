## Set-MQTT-Annotations Version 1.0, March 8th 2017
#! /bin/bash
#!/usr/bin/python
import time
import sched
import datetime
import os
import sys
import json
import paho.mqtt.client as mqtt

#
# alle Zeitangaben in UTC!!!!!! 
#

# MQTT broker host
mqtt_broker = 'swarm.hiveeyes.org'

# MQTT bus topic
mqtt_topic_template = u'{realm}/{network}/{gateway}/{node}/{kind}.json'
mqtt_address = dict(
    realm = 'hiveeyes',
    network =‚your id’,     # Imker
    gateway = ‚your site‘,                               # Standort
    node = ‚your node‘                           # Bienenstock
)
# define data and event type
mqtt_data_topic  = mqtt_topic_template.format(kind='data', **mqtt_address)
mqtt_event_topic = mqtt_topic_template.format(kind='event', **mqtt_address)

# Create MQTT client-id
pid = os.getpid()
client_id = '{}:{}'.format('client',str(pid))

if __name__ == "__main__":
	# Prepare event for MQTT"
	event = {
		"time": "2017-03-04T16:48:00Z",
		"title": "Futterwabe",
		"text" : "zusaetzliche Futterwabe von Hubert 2kg",
		"tags" : "event,Fuetterung,muc,mh"
		}
	# Serialize data as JSON
	payload = json.dumps(event)
	# Publish event to MQTT Backend
	backend = mqtt.Client(client_id=client_id, clean_session=True)
	backend.connect(mqtt_broker)
	backend.publish(mqtt_event_topic, payload)
	backend.disconnect()



