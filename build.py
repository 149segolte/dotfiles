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
from typing import Annotated, Any, Literal, Self, Union

import yaml
from pydantic import (
    AfterValidator,
    BaseModel,
    BeforeValidator,
    Field,
    FileUrl,
    ValidationError,
    model_validator,
)

LOGLEVEL = os.environ.get("LOGLEVEL", "WARNING").upper()
logging.basicConfig(format="HOOK(%(levelname)s): %(message)s", level=LOGLEVEL)


# Utility functions
def is_valid_mode(mode: int, fail: bool = True) -> int | None:
    u = (mode >> 6) & 0o7
    g = (mode >> 3) & 0o7
    o = mode & 0o7

    if not all(4 <= x <= 7 for x in (u, g, o)):
        if fail:
            raise ValueError(
                f"Invalid mode: {oct(mode)}. Each of user/group/other bits must be between 4 and 7."
            )
        else:
            return None

    return mode


def mode_set_bit(
    mode: int, bit: Literal["r", "w", "x"], type: Literal["u", "g", "o"] | None
) -> int:
    bit_value = {"r": 4, "w": 2, "x": 1}[bit]

    if type == "u":
        mode |= bit_value << 6
    elif type == "g":
        mode |= bit_value << 3
    elif type == "o":
        mode |= bit_value
    else:
        # If no type is specified, set the bit for all types
        mode |= (bit_value << 6) | (bit_value << 3) | bit_value

    return mode


def mode_merge(a: int, b: int, relax: bool = False) -> int:
    return a | b if relax else a & b


StripedStr = Annotated[str, BeforeValidator(lambda x: str.strip(str(x)))]
NonEmptyStr = Annotated[StripedStr, Field(min_length=1)]
ModeInt = Annotated[int, AfterValidator(is_valid_mode)]


class ResourceBase(BaseModel):
    # compression: str = Field(default="none")
    # verification: str = Field(default="")
    pass


class ResourceRemote(ResourceBase):
    kind: Literal["remote"]
    source: FileUrl
    headers: list[dict[str, str]] = []  # TODO: better type def for this


class ResourceInline(ResourceBase):
    kind: Literal["inline"]
    source: StripedStr


class ResourceLocal(ResourceBase):
    kind: Literal["local"]
    source: Path


Resource = Annotated[
    Union[ResourceRemote, ResourceInline, ResourceLocal], Field(discriminator="kind")
]


class File(BaseModel):
    path: Path
    contents: Resource | None = None
    append: list[Resource] = []
    mode: ModeInt = Field(default=0o644)

    @model_validator(mode="after")
    def validate_contents(self) -> Self:
        if self.contents is None and len(self.append) == 0:
            raise ValueError("either contents or append must be specified")
        return self


class ScriptType(StrEnum):
    RUN = "run"
    RUN_ONCE = "run_once"
    RUN_ONCHANGE = "run_onchange"
    RUN_BEFORE = "run_before"
    RUN_AFTER = "run_after"


class Script(BaseModel):
    name: NonEmptyStr
    type: ScriptType = ScriptType.RUN_ONCE
    content: Resource


class Manifest(BaseModel):
    files: list[File] = []
    scripts: list[Script] = []


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
    result = None
    try:
        result = subprocess.run(
            [str(executable)],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        raise ValueError(
            f"Module '{module_name}' failed with exit code {e.returncode}: "
            f"{e.stderr.strip() if e.stderr else ''}"
        )

    if not result:
        raise ValueError(f"Module '{module_name}' failed to run")

    stdout = result.stdout.strip()
    stderr = result.stderr.strip()

    if stderr:
        logging.warning(f"Module '{module_name}' produced stderr output:\n{stderr}")

    if not stdout:
        raise ValueError(f"Module '{module_name}' produced no output")

    try:
        return Manifest.model_validate_json(stdout, extra="forbid")
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
    cwd = Path.cwd()
    yaml.SafeLoader.add_constructor("!flatten", flatten_constructor)

    chezmoi_data = load_chezmoi_data()
    hostname = chezmoi_data.get("chezmoi", {}).get("hostname")
    if not isinstance(hostname, str) or not hostname:
        logging.critical("No hostname found in chezmoi data")
        sys.exit(1)

    hosts = load_hosts(cwd / "hosts.yaml")
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
            executable = resolve_module_executable(cwd, name)
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
    file_sources: dict[str, File] = {}
    script_sources: dict[str, Script] = {}

    for module_name, manifest in manifests.items():
        for file in manifest.files:
            path = file.path.expanduser().resolve()
            if not path.is_relative_to(cwd):
                logging.warning(
                    f"Skipping absolute path {file.path} (not supported yet)"
                )
                continue
            path = str(path.relative_to(cwd))

            current = file_sources.get(path)
            if current is not None:
                if file.contents and current.contents:
                    logging.critical(
                        f"Duplicate file path '{path}' with contents from module '{module_name}'"
                    )
                    sys.exit(1)

                if file.contents:
                    current.contents = file.contents
                current.append.extend(file.append)
                current.mode = mode_merge(current.mode, file.mode)
            else:
                file_sources[path] = file

        for script in manifest.scripts:
            name = script_filename(script)
            if name in script_sources:
                logging.critical(
                    f"Duplicate script name '{name}' from module '{module_name}'"
                )
                sys.exit(1)
            script_sources[name] = script

    file_paths = sorted(file_sources.keys())
    script_names = sorted(script_sources.keys())

    gen_details = [
        "Build Summary",
        f"  Host: {hostname}",
        "  Modules: " + (", ".join(module_names) if module_names else "(none)"),
        f"  Files: {len(file_paths)}",
        f"  Scripts: {len(script_names)}",
    ]

    logging.info("\n".join(gen_details))

    gen_files = ["Generation Summary"]
    if file_paths:
        gen_files.append("  Files:")
        for path in file_paths:
            gen_files.append(f"    - {path}")

    if script_names:
        gen_files.append("  Scripts:")
        for script_name in script_names:
            gen_files.append(f"    - {script_name}")

    logging.debug("\n".join(gen_files))


if __name__ == "__main__":
    main()
