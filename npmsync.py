import requests
import json

# Config
NPM_URL = ""
USERNAME = ""
PASSWORD = ""
WILDCARD_DOMAIN = ""
CONFIG_FILE = ""

def get_token():
    resp = requests.post(f"{NPM_URL}/api/tokens", json={
        "identity": USERNAME,
        "secret": PASSWORD
    })
    resp.raise_for_status()
    return resp.json()["token"]

def get_certificate_id(token, wildcard_name):
    resp = requests.get(f"{NPM_URL}/api/nginx/certificates", headers={
        "Authorization": f"Bearer {token}"
    })
    certs = resp.json()
    for cert in certs:
        if wildcard_name in cert["domain_names"]:
            print(f"Using certificate: {cert['nice_name']} (ID: {cert['id']})")
            return cert["id"]
    raise ValueError("Wildcard certificate not found")

def get_existing_hosts(token):
    resp = requests.get(f"{NPM_URL}/api/nginx/proxy-hosts", headers={
        "Authorization": f"Bearer {token}"
    })
    return resp.json()

def create_or_update_host(token, config):
    existing_hosts = get_existing_hosts(token)
    domain = config["domain_names"][0]

    for host in existing_hosts:
        if domain in host["domain_names"]:
            host_id = host["id"]
            print(f"Updating {domain} (ID: {host_id})...")
            r = requests.put(f"{NPM_URL}/api/nginx/proxy-hosts/{host_id}",
                             headers={"Authorization": f"Bearer {token}"},
                             json=config)
            r.raise_for_status()
            return

    print(f"Creating {domain}...")
    r = requests.post(f"{NPM_URL}/api/nginx/proxy-hosts",
                      headers={"Authorization": f"Bearer {token}"},
                      json=config)
    r.raise_for_status()

def main():
    with open(CONFIG_FILE) as f:
        configs = json.load(f)

    token = get_token()
    cert_id = get_certificate_id(token, WILDCARD_DOMAIN)

    for conf in configs:
        conf["certificate_id"] = cert_id
        create_or_update_host(token, conf)

if __name__ == "__main__":
    main()
