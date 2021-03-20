
### Requirements

 - Python 3
 - Zoneminder:
   - Account with api permissions
   - ES (event service) enabled
 - Slack:
   - Slack bot token 

### Install

```
pip3 install git+https://github.com/datachi7d/kittystons.git 
```

#### Troubleshooting install

 If you see the following error:

```
Command "python setup.py egg_info" failed with error code 1 in /tmp/pip-build-uz8r4g_q/opencv-python/
```

 Update pip:

```
pip3 install --upgrade pip
```

### Configuration file `kittystons.json`

```
{
  "apiurl": "http://localhost/zm/api",
  "portalurl": "http://localhost/zm",
  "url": "wss://localhost:9000",
  "allow_untrusted": true,
  "user": "<zm user>",
  "password": "<password>",
  "slack_token": "<slack bot token>"
}
```

### Running

 Create configuration file `kittystons.json` and run `kittystons` in the same directory

 Note: the `kittystons` script is located in `~/.local/bin` - add this to your path.
