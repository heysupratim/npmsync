import requests
import json
import os
from dotenv import load_dotenv

def load_config():
    """Load configuration from environment variables."""
    # Load .env file from the project root directory
    dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    load_dotenv(dotenv_path=dotenv_path)
    
    # Config
    return {
        "npm_url": os.environ.get("NPM_URL", ""),
        "username": os.environ.get("USERNAME", ""),
        "password": os.environ.get("PASSWORD", ""),
        "wildcard_domain": os.environ.get("WILDCARD_DOMAIN", ""),
        "config_file": os.environ.get("CONFIG_FILE", "")
    }

def get_token(npm_url, username, password):
    resp = requests.post(f"{npm_url}/api/tokens", json={
        "identity": username,
        "secret": password
    })
    resp.raise_for_status()
    return resp.json()["token"]

def get_certificate_id(npm_url, token, wildcard_name):
    resp = requests.get(f"{npm_url}/api/nginx/certificates", headers={
        "Authorization": f"Bearer {token}"
    })
    certs = resp.json()
    for cert in certs:
        if wildcard_name in cert["domain_names"]:
            print(f"Using certificate: {cert['nice_name']} (ID: {cert['id']})")
            return cert["id"]
    raise ValueError("Wildcard certificate not found")

def get_existing_hosts(npm_url, token):
    resp = requests.get(f"{npm_url}/api/nginx/proxy-hosts", headers={
        "Authorization": f"Bearer {token}"
    })
    return resp.json()

def create_or_update_host(npm_url, token, config):
    existing_hosts = get_existing_hosts(npm_url, token)
    domain = config["domain_names"][0]

    for host in existing_hosts:
        if domain in host["domain_names"]:
            host_id = host["id"]
            print(f"Updating {domain} (ID: {host_id})...")
            r = requests.put(f"{npm_url}/api/nginx/proxy-hosts/{host_id}",
                             headers={"Authorization": f"Bearer {token}"},
                             json=config)
            r.raise_for_status()
            return

    print(f"Creating {domain}...")
    r = requests.post(f"{npm_url}/api/nginx/proxy-hosts",
                      headers={"Authorization": f"Bearer {token}"},
                      json=config)
    r.raise_for_status()

def sync_hosts(config_file, npm_url, username, password, wildcard_domain):
    """Synchronize hosts based on configuration file."""
    with open(config_file) as f:
        configs = json.load(f)

    token = get_token(npm_url, username, password)
    cert_id = get_certificate_id(npm_url, token, wildcard_domain)

    for conf in configs:
        conf["certificate_id"] = cert_id
        create_or_update_host(npm_url, token, conf)
