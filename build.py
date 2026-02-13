#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "pydantic>=2.12.5",
#     "pyyaml>=6.0.2",
# ]
# ///
import json
import logging
import os
import subprocess
import sys
from enum import StrEnum
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, ValidationError, model_validator

logging.basicConfig(format="HOOK(%(levelname)s): %(message)s")


class FileContents(BaseModel):
    inline: str | None = None
    local: str | None = None

    @model_validator(mode="after")
    def check_content(self) -> "FileContents":
        has_inline = self.inline is not None
        has_local = self.local is not None
        if has_inline == has_local:
            raise ValueError("Exactly one of 'inline' or 'local' must be set.")
        return self


class File(BaseModel):
    path: str = Field(min_length=1)
    contents: FileContents
    mode: int = Field(default=0o644)


class ScriptType(StrEnum):
    RUN = "run"
    RUN_ONCE = "run_once"
    RUN_ONCHANGE = "run_onchange"
    RUN_BEFORE = "run_before"
    RUN_AFTER = "run_after"


class Script(BaseModel):
    name: str = Field(min_length=1)
    type: ScriptType = Field(default=ScriptType.RUN_ONCE)
    content: str = Field(min_length=1)


class Manifest(BaseModel):
    files: list[File] = Field(default=[])
    scripts: list[Script] = Field(default=[])


def load_chezmoi_data() -> dict[str, Any]:
    try:
        result = subprocess.run(
            ["chezmoi", "data", "--format=json"],
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        logging.critical(
            f"chezmoi data failed with exit code {e.returncode}: {e.stderr.strip() if e.stderr else ''}",
        )
        sys.exit(1)

    try:
        return json.loads(result.stdout.strip())
    except json.JSONDecodeError as e:
        logging.critical(f"Invalid JSON from chezmoi data: {e}")
        sys.exit(1)


def load_hosts(path: Path) -> dict[str, Any]:
    if not path.exists():
        logging.critical(f"hosts.yaml not found at {path}")
        sys.exit(1)

    try:
        data = yaml.safe_load(path.read_text())
    except yaml.YAMLError as e:
        logging.critical(f"Failed to parse hosts.yaml: {e}")
        sys.exit(1)

    if not isinstance(data, dict) or not isinstance(data.get("hosts"), dict):
        logging.critical(
            "hosts.yaml must have a 'hosts' key, mapping the hosts to module configs"
        )
        sys.exit(1)

    return data.get("hosts", {})


def resolve_module_executable(root: Path, name: str) -> Path:
    module_dir = root / "modules" / name
    if not module_dir.is_dir():
        raise ValueError(f"Module directory not found: {module_dir}")

    candidates = sorted(
        [
            path
            for path in module_dir.iterdir()
            if path.is_file() and path.name.startswith("generate")
        ]
    )

    for candidate in candidates:
        if os.access(candidate, os.X_OK):
            return candidate

    raise ValueError(f"No executable 'generate' script found for module '{name}'")


def run_module(executable: Path, payload: dict[str, Any]) -> Manifest:
    module_name = executable.parent.name
    try:
        result = subprocess.run(
            [str(executable)],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except subprocess.CalledProcessError as e:
        raise ValueError(
            f"Module '{module_name}' failed with exit code {e.returncode}: "
            f"{e.stderr.strip() if e.stderr else ''}"
        )

    if not result:
        raise ValueError(f"Module '{module_name}' produced no output")

    try:
        return Manifest.model_validate_json(result)
    except ValidationError as e:
        raise ValueError(f"Invalid manifest from module '{module_name}': {e}")


def script_filename(script: Script) -> str:
    prefix = script.type[:-1] if script.type.endswith("_") else script.type
    return f"{prefix}_{script.name}.sh"


def flatten_constructor(loader, node):
    value = loader.construct_sequence(node, deep=True)
    res = []
    for item in value:
        if isinstance(item, list):
            res.extend(item)
        else:
            res.append(item)
    return res


def main() -> None:
    root = Path(__file__).parent

    yaml.SafeLoader.add_constructor("!flatten", flatten_constructor)

    chezmoi_data = load_chezmoi_data()
    hostname = chezmoi_data.get("chezmoi", {}).get("hostname")
    if not isinstance(hostname, str) or not hostname:
        logging.critical("No hostname found in chezmoi data")
        sys.exit(1)

    hosts = load_hosts(root / "hosts.yaml")
    host_config = hosts.get(hostname)
    if host_config is None:
        available = ", ".join(sorted(hosts.keys()))
        logging.critical(
            f"Host '{hostname}' not found in hosts.yaml. Available hosts: {available if available else '(none)'}",
        )
        sys.exit(1)

    if not isinstance(host_config, dict):
        logging.critical(f"Host entry for '{hostname}' must be a mapping")
        sys.exit(1)

    manifests: dict[str, Manifest] = {}

    for name, data in host_config.items():
        if data is None:
            logging.warning(f"Module '{name}' is set to null; skipping")
            continue

        if not isinstance(data, dict):
            logging.critical(f"Module '{name}' config must be a mapping")
            sys.exit(1)

        try:
            executable = resolve_module_executable(root, name)
            manifests[name] = run_module(
                executable,
                {
                    "chezmoi": chezmoi_data,
                    "data": data,
                },
            )
        except ValueError as e:
            logging.critical(f"{e}")
            sys.exit(1)

    module_names = list(manifests.keys())
    warnings: list[str] = []
    file_sources: dict[str, list[str]] = {}
    script_names: list[str] = []

    for module_name, manifest in manifests.items():
        for file in manifest.files:
            if file.path.startswith("/"):
                warnings.append(
                    f"Skipping absolute path {file.path} (not supported yet)"
                )
                continue
            file_sources.setdefault(file.path, []).append(module_name)

        for script in manifest.scripts:
            script_names.append(script_filename(script))

    for path, modules in file_sources.items():
        if len(modules) > 1:
            warnings.append(f"Conflict: {path} produced by {', '.join(modules)}")

    file_paths = sorted(file_sources.keys())

    print(f"Host: {hostname}")
    print("Modules: " + ", ".join(module_names) if module_names else "Modules: (none)")
    print(f"Files: {len(file_paths)}")
    print(f"Scripts: {len(script_names)}")

    if file_paths:
        print("Files:")
        for path in file_paths:
            print(f"  - {path}")

    if script_names:
        print("Scripts:")
        for script_name in script_names:
            print(f"  - {script_name}")

    if warnings:
        print("Warnings:")
        for warning in warnings:
            print(f"  - {warning}")


if __name__ == "__main__":
    main()
