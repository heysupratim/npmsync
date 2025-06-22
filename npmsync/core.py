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
        "username": os.environ.get("NPM_USERNAME", ""),
        "password": os.environ.get("NPM_PASSWORD", ""),
        "config_file": os.environ.get("NPM_CONFIG_FILE", "")
    }

def get_token(npm_url, username, password):
    resp = requests.post(f"{npm_url}/api/tokens", json={
        "identity": username,
        "secret": password
    })
    resp.raise_for_status()
    return resp.json()["token"]

def extract_wildcards_from_domains(domains):
    """Extract wildcard domains from a list of domain names."""
    wildcards = set()
    for domain in domains:
        parts = domain.split('.')
        if len(parts) >= 2:  # Ensure we have at least a subdomain and domain
            # Create wildcard by replacing the first part with *
            wildcard = f"*.{'.'.join(parts[1:])}"
            wildcards.add(wildcard)
    return list(wildcards)

def get_certificate_id(npm_url, token, wildcard_domains):
    resp = requests.get(f"{npm_url}/api/nginx/certificates", headers={
        "Authorization": f"Bearer {token}"
    })
    resp.raise_for_status()
    certs = resp.json()
    
    # Try to find a certificate that matches any of our wildcard domains
    for wildcard in wildcard_domains:
        for cert in certs:
            if wildcard in cert["domain_names"]:
                print(f"Using certificate: {cert['nice_name']} (ID: {cert['id']}) for {wildcard}")
                return cert["id"]
    
    # If we reach here, no matching certificate was found
    wildcard_list = ', '.join(wildcard_domains)
    raise ValueError(f"No matching wildcard certificates found for: {wildcard_list}")

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

def sync_hosts(config_file, npm_url, username, password):
    """Synchronize hosts based on configuration file."""
    with open(config_file) as f:
        configs = json.load(f)

    # Extract all domain names from configs
    all_domains = []
    for conf in configs:
        all_domains.extend(conf["domain_names"])
    
    # Generate wildcard domains from the domain names
    wildcard_domains = extract_wildcards_from_domains(all_domains)
    if not wildcard_domains:
        raise ValueError("Could not extract any wildcard domains from configuration")
    
    print(f"Extracted wildcard domains: {', '.join(wildcard_domains)}")
    
    token = get_token(npm_url, username, password)
    cert_id = get_certificate_id(npm_url, token, wildcard_domains)

    for conf in configs:
        conf["certificate_id"] = cert_id
        create_or_update_host(npm_url, token, conf)
