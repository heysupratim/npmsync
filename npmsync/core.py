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

def get_certificate_mapping(npm_url, token, wildcard_domains):
    """Get a mapping of wildcard domains to their certificate IDs."""
    resp = requests.get(f"{npm_url}/api/nginx/certificates", headers={
        "Authorization": f"Bearer {token}"
    })
    resp.raise_for_status()
    certs = resp.json()
    
    cert_mapping = {}
    for wildcard in wildcard_domains:
        for cert in certs:
            if wildcard in cert["domain_names"]:
                print(f"Found certificate: {cert['nice_name']} (ID: {cert['id']}) for {wildcard}")
                cert_mapping[wildcard] = cert["id"]
                break
        
        if wildcard not in cert_mapping:
            print(f"Warning: No matching certificate found for {wildcard}")
    
    if not cert_mapping:
        wildcard_list = ', '.join(wildcard_domains)
        raise ValueError(f"No matching wildcard certificates found for any of: {wildcard_list}")
    
    return cert_mapping

def get_domain_certificate_id(domain, cert_mapping):
    """Get the appropriate certificate ID for a domain based on the cert mapping."""
    domain_parts = domain.split('.')
    if len(domain_parts) >= 2:
        wildcard = f"*.{'.'.join(domain_parts[1:])}"
        if wildcard in cert_mapping:
            return cert_mapping[wildcard]
    
    # If no matching wildcard found, use the first available certificate
    return next(iter(cert_mapping.values()))

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
    cert_mapping = get_certificate_mapping(npm_url, token, wildcard_domains)

    for conf in configs:
        # Get the appropriate certificate ID for this domain
        domain = conf["domain_names"][0]
        cert_id = get_domain_certificate_id(domain, cert_mapping)
        print(f"Using certificate ID {cert_id} for {domain}")
        
        conf["certificate_id"] = cert_id
        create_or_update_host(npm_url, token, conf)
