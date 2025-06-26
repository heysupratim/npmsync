> ⚠️ **Warning:** This project is a work in progress. **Do not use it in production environments.**

# NPM Sync

A tool to automate configuration of Nginx Proxy Manager hosts.

## Installation

Add the following service to your `docker-compose.yml`:

```yaml
services:
  npmsync:
    image: "ghcr.io/heysupratim/npmsync:latest"
    container_name: npmsync
    restart: unless-stopped
    environment:
      - name=value
      - NPM_URL=${NPM_URL}
      - NPM_USERNAME=${NPM_USERNAME}
      - NPM_PASSWORD=${NPM_PASSWORD}
    volumes:
      - ./config:/app/config:z
```

## Configuration

Create a `.env` file in the project root:

```
NPM_URL=https://your-npm-instance
NPM_USERNAME=your_username
NPM_PASSWORD=your_password
```

Create a directory named `config` in your project root, and add a file called `proxy_hosts.json` inside it:

```sh
mkdir -p config
touch config/proxy_hosts.json
```

## Configuration File Format for proxy_hosts.json

The configuration file should be a JSON array of proxy host configurations that you want to commit to version control

```json
[
  {
    "domain_names": [
      "subdomain1.domain.com"
    ],
    "forward_host": "192.168.1.64",
    "forward_port": 9898, 
    "forward_scheme": "http",
    "caching_enabled": false,
    "block_exploits": false,
    "allow_websocket_upgrade": true,
    "ssl_forced": true,
    "http2_support": true,
    "hsts_enabled": true,
    "hsts_subdomains": false,
    "enabled": true,
    "meta": {
      "letsencrypt_agree": true,
      "dns_challenge": false
    },
    "advanced_config": "",
    "locations": []
  },
    {
    "domain_names": [
      "subdomain2.domain.com"
    ],
    "forward_host": "192.168.1.64",
    "forward_port": 9898, 
    "forward_scheme": "http",
    "caching_enabled": false,
    "block_exploits": false,
    "allow_websocket_upgrade": true,
    "ssl_forced": true,
    "http2_support": true,
    "hsts_enabled": true,
    "hsts_subdomains": false,
    "enabled": true,
    "meta": {
      "letsencrypt_agree": true,
      "dns_challenge": false
    },
    "advanced_config": "",
    "locations": []
  }
]
```
> 💡 **Tip:** Ensure that your Nginx Proxy Manager already has SSL certificates set up for the domains you plan to use with these entries.

## Configration Values

| Key                     | Description                                   |
|-------------------------|-----------------------------------------------|
| domain_names            | List of domain names for the proxy host       |
| forward_host            | Target host IP or hostname                    |
| forward_port            | Target port number                            |
| forward_scheme          | Protocol to use (http/https)                  |
| caching_enabled         | Enable or disable caching (true/false)        |
| block_exploits          | Block common exploits (true/false)            |
| allow_websocket_upgrade | Allow WebSocket upgrade (true/false)          |
| ssl_forced              | Force SSL redirection (true/false)            |
| http2_support           | Enable HTTP/2 support (true/false)            |
| hsts_enabled            | Enable HSTS (true/false)                      |
| hsts_subdomains         | Apply HSTS to subdomains (true/false)         |
| enabled                 | Enable or disable the proxy host (true/false) |
| meta                    | Additional metadata (object)                  |
| advanced_config          | Advanced Nginx configuration (string)         |
| locations                | Custom location blocks (array)                |