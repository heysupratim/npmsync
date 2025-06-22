# NPM Sync

A tool to automate configuration of Nginx Proxy Manager hosts.

## Installation

```bash
# Install with Poetry
poetry install
```

## Configuration

Create a `.env` file in the project root:

```
NPM_URL=https://your-npm-instance
USERNAME=your_username
PASSWORD=your_password
WILDCARD_DOMAIN=*.yourdomain.com
CONFIG_FILE=hosts.json
```

## Usage

```bash
# Run with Poetry
poetry run npmsync

# Or with specific config file
poetry run npmsync --config /path/to/config.json
```

## Configuration File Format

The configuration file should be a JSON array of proxy host configurations:

```json
[
  {
    "domain_names": ["app1.yourdomain.com"],
    "forward_host": "192.168.1.100",
    "forward_port": 8080,
    "access_list_id": "0",
    "certificate_id": 0,
    "ssl_forced": true,
    "caching_enabled": false,
    "block_exploits": true,
    "advanced_config": "",
    "meta": {
      "letsencrypt_agree": false,
      "dns_challenge": false
    },
    "allow_websocket_upgrade": true,
    "http2_support": true,
    "forward_scheme": "http",
    "enabled": true,
    "locations": []
  }
]
```
