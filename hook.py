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
logging.basicConfig(format="HOOK(%(levelname)s): %(message)s")
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
    "environment": {
        "packages": {},
        "shell": {},
        "system": {},
    },
    "modules": {},
}

### END: Static Data

host = hosts.get(chezmoi["HOSTNAME"])
if host is None:
    logging.critical(f"unknown hostname: {chezmoi['HOSTNAME']}")
    sys.exit(1)

### BEGIN: Process Data

# ...

### END: Process Data

TARGET_FILE = Path(chezmoi["SOURCE_DIR"]) / ".chezmoidata.json"
TARGET_FILE.write_text(json.dumps(data, indent=2))
