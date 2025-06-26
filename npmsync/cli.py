"""Command line interface for npmsync."""

from .core import load_config, watch_config_directory
import argparse
import os
import sys

def main():
    """Main entry point for the npmsync CLI."""
    parser = argparse.ArgumentParser(description="Nginx Proxy Manager synchronization tool")
    parser.add_argument("--npm-url", help="Nginx Proxy Manager URL")
    args = parser.parse_args()
    
    # Load config from .env file
    config = load_config()

    # print config
    print("Loaded configuration:")
    # for key, value in config.items():
    #     print(f"{key}: {value}")
    
    # Override with command-line arguments if provided
    if args.npm_url:
        config["npm_url"] = args.npm_url
        
    # Validate configuration
    if not config["npm_url"]:
        print("Error: NPM_URL not set. Please set it in .env")
        sys.exit(1)
    if not config["username"] or not config["password"]:
        print("Error: USERNAME or PASSWORD not set. Please set them in .env")
        sys.exit(1)
    
    try:
        # Get the directory containing the proxy hosts file
        config_dir = os.path.dirname("/app/config/proxy_hosts.json")

        # Watch the entire config directory
        watch_config_directory(
            config_dir,
            config["npm_url"],
            config["username"],
            config["password"]
        )
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
