import os
import json
import time
from pyzm.api import ZMApi
from pyzm.ZMEventNotification import ZMEventNotification
from pyzm.helpers.Base import ConsoleLog

from tempfile import TemporaryDirectory
from slack_sdk import WebClient


def get_config(config_file_path='kittystons.json'):
    with open(config_file_path) as config_file:
        config_json = json.loads(config_file.read())

        logger = ConsoleLog()
        logger.set_level(2)
        api_options = {
            **config_json,
            "logger": logger,  # use none if you don't want to log to ZM,
            # 'disable_ssl_cert_check': True
        }
        return api_options

    return None


def send_event(message, zmapi_client, slack_client, channel):
    if 'events' in message:
        with TemporaryDirectory(suffix='zm') as temp_dir:
            for event_raw in message['events']:
                if 'EventId' in event_raw:
                    event_id = event_raw['EventId']
                    initial_comment = ''
                    fid = 'snapshot'
                    if 'Cause' in event_raw:
                        initial_comment = f"```{event_raw['Cause']}```"
                    if 'DetectionJson' in event_raw:
                        if event_raw['DetectionJson']:
                            fid = 'objdetect'
                    events = zmapi_client.events().get(options={'event_id':event_id})
                    for event in events:
                        upload_file_name = event.download_image(dir=temp_dir, fid=fid)
                        if os.path.isfile(upload_file_name):
                            print(f"Sending {upload_file_name} to {channel} with comment {initial_comment}")
                            slack_client.files_upload(channels=channel, initial_comment=initial_comment, file=upload_file_name)


class SlackZMEventNotification(ZMEventNotification):
    def __init__(self, api_options):

        self.zmapi = ZMApi(options=api_options)
        ZMEventNotification.__init__(self, {
            **api_options,
             'on_es_message': self.on_es_message,
             'on_es_close': self.on_es_close,
             'on_es_error': self.on_es_error,
        })
        self.slack_client = client = WebClient(token=api_options['slack_token'])

    def on_es_message(self, message):
        print(f"Got {message}")
        send_event(message, self.zmapi, self.slack_client, "#cameras")

    def on_es_close(self):
        print(f"Connection closed")

    def on_es_error(self, error):
        print(f"Error: {error}")


def run_kittystons(config_file):
    config_options = get_config(config_file)
    if config_options is not None:
        while True:
            try:
                slack_zm = SlackZMEventNotification(config_options)
                slack_zm.worker_thread.join(60.0)
                print("Still running...")
            except Exception as e:
                print(f"{e}")
            finally:
                time.sleep(10)