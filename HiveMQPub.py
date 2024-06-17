import paho.mqtt.client as paho
import json
import time
from Detector import undesirable_rates, average_undesirable_rate, object_counts

def on_connect(client, userdata, flags, rc, properties=None):
    print("CONNACK received with code %s." % rc)

def on_publish(client, userdata, mid, properties=None):
    print("Message Published: " + str(mid))


client = paho.Client(client_id="", userdata=None, protocol=paho.MQTTv5)
client.on_connect = on_connect
client.on_publish = on_publish

client.connect("broker.hivemq.com", 1883)

message = {
    "id": 1,
    "state": 0
}

taux_image = client.publish("gprotech/casque1/taux_image", json.dumps(undesirable_rates), qos=1)
taux = client.publish("gprotech/casque1/taux", json.dumps(average_undesirable_rate), qos=1)
nbr_objets = client.publish("gprotech/casque1/nbr_objets", json.dumps(object_counts), qos=1)

client.loop_start()
print(taux_image)
print(taux)
print(nbr_objets)
client.loop_stop()

"""
client.loop_start()
i = 0
while i < 4:
    time.sleep(1)
    client.publish("gprotech/casque1/taux", json.dumps(message), qos=1)
    i = i + 1

client.loop_stop()


while True:
    client.publish("gprotech/casque1/taux_image", json.dumps(undesirable_rates), qos=1)
    client.publish("gprotech/casque1/taux", json.dumps(average_undesirable_rate), qos=1)
    client.publish("gprotech/casque1/nbr_objets", json.dumps(object_counts), qos=1)

    #time.sleep(5)  # Publier toutes les 5 secondes
"""
