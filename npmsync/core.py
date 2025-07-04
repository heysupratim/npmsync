import requests
import json
import os
import time
from dotenv import load_dotenv
from watchdog.observers.polling import PollingObserver
from watchdog.events import FileSystemEventHandler
import yaml

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
        "proxy_hosts_file": os.environ.get("NPM_PROXY_HOSTS_FILE", "config/proxy_hosts.json")
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
    
    # If no matching wildcard found and cert_mapping is not empty, use the first available certificate
    if cert_mapping:
        return next(iter(cert_mapping.values()))
    
    # Return None if no certificates are available
    return None

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

def load_yaml_config(yaml_file):
    """Load configuration from YAML file."""
    with open(yaml_file) as f:
        return yaml.safe_load(f)

class ConfigFileHandler(FileSystemEventHandler):
    """Handler for config directory change events."""
    def __init__(self, config_dir, npm_url, username, password):
        self.config_dir = os.path.abspath(config_dir)
        self.npm_url = npm_url
        self.username = username
        self.password = password
        self.last_modified = time.time()
        
    def on_modified(self, event):
        # Avoid duplicate events (some systems trigger multiple events)
        current_time = time.time()
        if current_time - self.last_modified < 1:  # Debounce for 1 second
            return
            
        self.last_modified = current_time
        # Log the event variables for debugging
        # print(f"Event type: {event.event_type}, Path: {event.src_path}")

        print(f"Dir {os.path.basename(event.src_path)} modified, syncing hosts...")
        # Check for JSON file first, then YAML file
        json_config_file = os.path.join(self.config_dir, "proxy_hosts.json")
        yaml_config_file = os.path.join(self.config_dir, "proxy_hosts.yaml")
        
        if os.path.exists(json_config_file):
            sync_hosts(json_config_file, self.npm_url, self.username, self.password)
        elif os.path.exists(yaml_config_file):
            sync_hosts(yaml_config_file, self.npm_url, self.username, self.password, is_yaml=True)
        else:
            print("No proxy_hosts.json or proxy_hosts.yaml found in the config directory")
            
def watch_config_directory(config_dir, npm_url, username, password):
    """Watch the config directory for changes and sync hosts when changes are detected."""
    # Get default config files for initial sync
    json_config_file = os.path.join(config_dir, "proxy_hosts.json")
    yaml_config_file = os.path.join(config_dir, "proxy_hosts.yaml")
    
    if os.path.exists(json_config_file):
        # Initial sync with JSON file
        sync_hosts(json_config_file, npm_url, username, password)
    elif os.path.exists(yaml_config_file):
        # Initial sync with YAML file
        sync_hosts(yaml_config_file, npm_url, username, password, is_yaml=True)
    else:
        print("No proxy_hosts.json or proxy_hosts.yaml found in the config directory")
    
    # Set up directory watching
    event_handler = ConfigFileHandler(config_dir, npm_url, username, password)
    observer = PollingObserver()
    observer.schedule(event_handler, path=config_dir, recursive=False)
    observer.start()
    
    print(f"Watching directory {config_dir} for changes. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

def sync_hosts(config_file, npm_url, username, password, is_yaml=False):
    """Synchronize hosts based on configuration file."""
    if is_yaml:
        configs = load_yaml_config(config_file)
    else:
        with open(config_file) as f:
            configs = json.load(f)

    # Extract all domain names from configs
    all_domains = []
    for conf in configs:
        all_domains.extend(conf["domain_names"])
    
    # Generate wildcard domains from the domain names
    wildcard_domains = extract_wildcards_from_domains(all_domains)
    if not wildcard_domains:
        print("Warning: Could not extract any wildcard domains from configuration")
        cert_mapping = {}
    else:
        print(f"Extracted wildcard domains: {', '.join(wildcard_domains)}")
        token = get_token(npm_url, username, password)
        try:
            cert_mapping = get_certificate_mapping(npm_url, token, wildcard_domains)
        except ValueError as e:
            print(f"Warning: {str(e)}")
            cert_mapping = {}
    
    token = token if 'token' in locals() else get_token(npm_url, username, password)

    for conf in configs:
        # Get the appropriate certificate ID for this domain
        domain = conf["domain_names"][0]
        cert_id = get_domain_certificate_id(domain, cert_mapping)
        
        if cert_id:
            print(f"Using certificate ID {cert_id} for {domain}")
            conf["certificate_id"] = cert_id
        else:
            print(f"No certificate found for {domain}, proceeding without SSL")
            # Remove certificate_id if it exists in the config
            conf.pop("certificate_id", None)
        
        create_or_update_host(npm_url, token, conf)
