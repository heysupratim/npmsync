"""Command line interface for npmsync."""

from .core import load_config, sync_hosts
import argparse
import sys

def main():
    """Main entry point for the npmsync CLI."""
    parser = argparse.ArgumentParser(description="Nginx Proxy Manager synchronization tool")
    parser.add_argument("--config", help="Specify path to configuration file")
    parser.add_argument("--npm-url", help="Nginx Proxy Manager URL")
    args = parser.parse_args()
    
    # Load config from .env file
    config = load_config()
    
    # Override with command-line arguments if provided
    if args.config:
        config["config_file"] = args.config
    if args.npm_url:
        config["npm_url"] = args.npm_url
        
    # Validate configuration
    if not config["npm_url"]:
        print("Error: NPM_URL not set. Please set it in .env or provide --npm-url")
        sys.exit(1)
    if not config["username"] or not config["password"]:
        print("Error: USERNAME or PASSWORD not set. Please set them in .env")
        sys.exit(1)
    if not config["config_file"]:
        print("Error: CONFIG_FILE not set. Please set it in .env or provide --config")
        sys.exit(1)
    if not config["wildcard_domain"]:
        print("Error: WILDCARD_DOMAIN not set. Please set it in .env")
        sys.exit(1)
    
    try:
        sync_hosts(
            config["config_file"],
            config["npm_url"],
            config["username"],
            config["password"],
            config["wildcard_domain"]
        )
        print("Synchronization completed successfully")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
