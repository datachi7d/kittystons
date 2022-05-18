import json
import kittystons.zm
import kittystons.frigate

def get_config(config_file_path='kittystons.json'):
    with open(config_file_path) as config_file:
        config_json = json.loads(config_file.read())
        return config_json

def run_kittystons(config_file):
    config_json = get_config(config_file)
    mode = config_json.get("mode", "")
    if mode == "zm":
        kittystons.zm.run_kittystons(config_json)
    elif mode == "frigate":
        kittystons.frigate.run_kittystons(config_json)