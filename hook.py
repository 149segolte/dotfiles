#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "pyyaml>=6.0.3",
# ]
# ///
import copy
import logging
import os
import sys
from pathlib import Path
from typing import Any

import yaml

DEBUG = False
FILE_ROOT = Path(__file__).parent
FILES_DIR = FILE_ROOT / "files"

# Set up logging
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


# Load helper for external files
def load(path: str) -> str:
    """Load the contents of a file (relative to the files directory) as a string."""
    return (FILES_DIR / path).read_text()


# YAML custom tags
def tag_eval(loader, node):
    value = loader.construct_scalar(node)
    if isinstance(value, str):
        return eval(value)
    return None


def tag_load(loader, node):
    value = loader.construct_scalar(node)
    if isinstance(value, str):
        return load(value)
    return None


yaml.add_constructor("!eval", tag_eval, yaml.SafeLoader)
yaml.add_constructor("!load", tag_load, yaml.SafeLoader)

### BEGIN: YAML data load

raw_data: dict[str, Any] = (
    yaml.safe_load((FILE_ROOT / "hook_data.yaml").read_text()) or {}
)
hosts: dict[str, Any] = (
    yaml.safe_load((FILE_ROOT / "hook_hosts.yaml").read_text()) or {}
)

host = hosts.get(chezmoi["HOSTNAME"])
if not isinstance(host, dict):
    logging.critical(f"unknown hostname: {chezmoi['HOSTNAME']}")
    sys.exit(1)


def merge_data(base: Any, overlay: Any, path: tuple[str, ...] = ()) -> Any:
    """Deep-merge overlay into base with additive list semantics."""
    if isinstance(base, dict) and isinstance(overlay, dict):
        merged = copy.deepcopy(base)
        for key, value in overlay.items():
            merged[key] = merge_data(merged.get(key), value, path + (key,))
        return merged

    if isinstance(base, list) and isinstance(overlay, list):
        return copy.deepcopy(base) + copy.deepcopy(overlay)

    return copy.deepcopy(overlay)


data: dict[str, Any] = merge_data(raw_data, host)

### END: YAML data load

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
        del pkg["shell"]

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

TARGET_FILE = Path(chezmoi["SOURCE_DIR"]) / ".chezmoidata.yaml"
TARGET_FILE.write_text(yaml.dump(data, indent=2))
