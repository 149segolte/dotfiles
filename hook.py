#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

# Set up logging
DEBUG = False
logging.basicConfig(
    format="HOOK(%(levelname)s): %(message)s",
    level=logging.DEBUG if DEBUG else logging.INFO,
)
# Disable keyboard interrupt
sys.excepthook = lambda type_, e, traceback: (
    sys.__excepthook__(type_, e, traceback) if type_ is not KeyboardInterrupt else None
)

# Get chezmoi environment variables
if os.getenv("CHEZMOI", 0) != "1":
    logging.critical("script not running under chezmoi")
    sys.exit(1)
chezmoi = {
    k.removeprefix("CHEZMOI_"): v
    for k, v in os.environ.items()
    if k.startswith("CHEZMOI_")
}

### BEGIN: Static Data

hosts: dict[str, Any] = {
    "novasking": {},
    "yigirus": {},
    "rpi": {},
}

data: dict[str, Any] = {
    "data": {
        "user": {
            "name": chezmoi["USERNAME"],
            "keys": {},  # Loads from disk later
        },
    },
    "environment": {
        "packages": [
            {
                "kind": "brew",
                "name": "zoxide",
                "shell": "# Zoxide\nzoxide init fish | source\n",
            },
        ],
        "shell": {
            "aliases": {
                "ls": "eza",
                "ll": "eza -la",
                "cat": "bat --style=plain",
                "grep": "rg",
            },
            "config": "",
            "interactive_config": "",
        },
        "system": {},
    },
    "modules": {
        "git": {
            "user": {
                "name": "149segolte",
                "email": "37300847+149segolte@users.noreply.github.com",
                "signingkey": "id_ed25519_sk_genid.pub",
            },
            "exclude": [],  # Array of git exclude patterns
        },
    },
}

### END: Static Data

host = hosts.get(chezmoi["HOSTNAME"])
if host is None:
    logging.critical(f"unknown hostname: {chezmoi['HOSTNAME']}")
    sys.exit(1)

### BEGIN: Gather "data" field values

# Get public key data for user
ssh_dir = Path(chezmoi["SOURCE_DIR"]) / "dot_ssh"
if not ssh_dir.exists():
    logging.error(f"ssh directory not found: {ssh_dir}")
    sys.exit(1)

pub_keys = {}
for key in ssh_dir.glob("*.pub"):
    pub_keys[key.name] = key.read_text().strip()

if len(pub_keys) == 0:
    logging.error("no public keys found for user")
    sys.exit(1)

data["data"]["user"]["keys"] = pub_keys

### END: Gather "data" field values

### BEGIN: Gather "environment" field values

# Collect all packages shell config
shell_config = ""
for pkg in data["environment"]["packages"]:
    sh = pkg.get("shell")
    if sh is not None:
        shell_config += sh + "\n"

if len(shell_config) > 0:
    data["environment"]["shell"]["config"] += shell_config

### END: Gather "environment" field values

### BEGIN: Gather "modules" field values

# Ensure git signing key
signing_key = data["modules"]["git"]["user"]["signingkey"]
if signing_key is None:
    logging.error("git user.signingkey not set")
    sys.exit(1)

if signing_key not in data["data"]["user"]["keys"]:
    logging.error(f"git user.signingkey not found: {signing_key}")
    # sys.exit(1)

# Add extra git excludes
if chezmoi["OS"] == "darwin":
    data["modules"]["git"]["exclude"].append(".DS_Store")

# ...

### END: Gather "modules" field values

TARGET_FILE = Path(chezmoi["SOURCE_DIR"]) / ".chezmoidata.json"
TARGET_FILE.write_text(json.dumps(data, indent=2))
