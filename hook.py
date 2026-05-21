#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///
import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import Any

logging.basicConfig(format="HOOK(%(levelname)s): %(message)s")


def global_exceptions(type_, e, traceback):
    if type_ is KeyboardInterrupt:
        pass
    elif type_ is subprocess.CalledProcessError:
        logging.critical(f"command failed ({e.returncode}): {e.stderr.strip()}")
    elif type_ is json.JSONDecodeError:
        logging.critical(f"JSON decode failed: {e}")
    else:
        sys.__excepthook__(type_, e, traceback)


sys.excepthook = global_exceptions

run_cmd = subprocess.run(
    ["chezmoi", "data", "--format=json"],
    capture_output=True,
    text=True,
    check=True,
)
chezmoi: dict[str, Any] = json.loads(run_cmd.stdout.strip()).get("chezmoi")

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

host = hosts.get(chezmoi["hostname"])
if host is None:
    logging.critical(f"unknown hostname: {chezmoi['hostname']}")
    sys.exit(1)

### BEGIN: Process Data

# ...

### END: Process Data

TARGET_FILE = Path(chezmoi["sourceDir"]) / ".chezmoidata.json"
TARGET_FILE.write_text(json.dumps(data, indent=2))
