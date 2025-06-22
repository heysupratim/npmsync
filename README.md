> ⚠️ **Warning:** This project is a work in progress. **Do not use it in production environments.**

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
NPM_USERNAME=your_username
NPM_PASSWORD=your_password
NPM_PROXY_HOSTS_FILE=hosts.json
```

## Usage

```bash
# Run with Poetry
poetry run npmsync

# Or with specific config file
poetry run npmsync --config /path/to/hosts.json
```

## Configuration File Format

The configuration file should be a JSON array of proxy host configurations:

```json
[
  {
    "domain_names": ["subdomain.domain.com"],
    "forward_host": "",
    "forward_port": ,
    "forward_scheme": "http",
    "ssl_forced": true,
    "block_exploits": false,
    "caching_enabled": false,
    "allow_websocket_upgrade": true,
    "http2_support": true,
    "enabled": true,
    "access_list_id": null,
    "meta": {
      "letsencrypt_agree": true,
      "dns_challenge": false
    }
  }
]
```
