import json
import requests
import base64
import io
import time
import logging
import sys
import threading

from slack_sdk import WebClient

import paho.mqtt.client as mqtt

def slack_upload_event(slack_client, slack_channel, file, comment):
    logging.info(f"Posting comment {comment} with {file}")
    if file is not None:
        slack_client.files_upload(channels=slack_channel, initial_comment=comment, file=file)
    else:
        slack_client.chat_postMessage(channel=slack_channel, text=comment)


def get_frigate_event(friage_server, event_id):
    r = requests.get(f"http://{friage_server}/api/events/{event_id}")
    if r.status_code == 200:
        return r.json()


def get_frigate_camera_snapshot(frigate_server, camera, height=300):
    query = f"?h={height}" if height > 0 else ""
    r = requests.get(f"http://{frigate_server}/api/{camera}/latest.jpg{query}")
    if r.status_code == 200:
        output = io.BytesIO()
        output.write(r.content)
        output.seek(0)
        return output


def get_friage_event_image(frigate_server, event_id):
    output = None
    retry_count = 10
    retry_wait = 5
    while retry_count > 0:
        event_data = get_frigate_event(frigate_server, event_id)
        if event_data is not None:
            if len(event_data["thumbnail"]) > 5:
                logging.debug("Got thumbnail")
                output = io.BytesIO()
                output.write(base64.b64decode(event_data["thumbnail"]))
                output.seek(0)
                break        
        logging.debug(f"[{retry_count}]Retrying thumbnail in {retry_wait}...")
        retry_count -= 1
        time.sleep(retry_wait)
    return output


def get_markdown_from_label(label):
    label_map = {
        "person": ":bust_in_silhouette:",
    }
    return label_map.get(label, f":{label}:")


def handle_frigate_event_thread(slack_client, slack_channel, frigate_server, message_payload):
    try:
        if message_payload['type'] == 'new':
            output_image = get_frigate_camera_snapshot(frigate_server,  message_payload['after']['camera'])
            slack_upload_event(slack_client, slack_channel, output_image, f":cat: thinks she see's a {get_markdown_from_label(message_payload['after']['label'])} on the {message_payload['after']['camera']}")
        elif message_payload['type'] == 'update':
            output_image = get_frigate_camera_snapshot(frigate_server,  message_payload['after']['camera'])
            slack_upload_event(slack_client, slack_channel, output_image, f":cat: is watching a {get_markdown_from_label(message_payload['after']['label'])} on the {message_payload['after']['camera']}")
        elif message_payload['type'] == 'end':
            output_image = get_friage_event_image(frigate_server, message_payload['after']['id'])
            slack_upload_event(slack_client, slack_channel, output_image, f":cat: just saw a {get_markdown_from_label(message_payload['after']['label'])} on the {message_payload['after']['camera']} \n <http://{frigate_server}/events/{message_payload['after']['id']}|frigate event>")
    except Exception as e:
        logging.error("Exception handling event:", exc_info=True)


def handle_frigate_event(slack_client, slack_channel, frigate_server, message_payload_raw):
    message_payload = None
    try:
        message_payload = json.loads(message_payload_raw)
        if 'type' in message_payload.keys() and 'after' in message_payload.keys():
            t = threading.Thread(target=handle_frigate_event_thread, args=(slack_client, slack_channel, frigate_server, message_payload, ), name=message_payload['after']['id'])
            t.start() 
    except Exception as e:
        logging.error("Exception creating event:", exc_info=True)

        
def run_mqtt(mqtt_server, frigate_server, slack_token, slack_channel):

    def on_connect(client, userdata, flags, rc):
        logging.info(f"Connected with result code {str(rc)}")
        client.subscribe([("frigate/events",0), ("frigate/stats",0)])

    def on_message(client, userdata, msg):
        if msg.topic == "frigate/events":
            handle_frigate_event(userdata, slack_channel, frigate_server, msg.payload)
        elif msg.topic == "frigate/stats":
            #logging.debug(f"Stats: \n{json.dumps(json.loads(msg.payload), sort_keys=True)}")
            pass
            
    slack_client = WebClient(token=slack_token)

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.user_data_set(slack_client)

    client.connect(mqtt_server, 1883, 60)
    client.loop_forever()


def run_kittystons(config_json):
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format="[%(asctime)s]%(threadName)s:%(module)s: %(message)s")
    run_mqtt(config_json['mqtt'], config_json['frigate'], config_json['slack_token'], config_json['slack_channel'])
