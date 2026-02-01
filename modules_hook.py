#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "deepmerge>=2.0",
#     "jsonschema>=4.26.0",
#     "pydantic>=2.12.5",
# ]
# ///

import json
import logging
import os
import subprocess
from argparse import ArgumentParser
from copy import deepcopy
from enum import StrEnum
from pathlib import Path
from typing import Any

from deepmerge import always_merger
from jsonschema import SchemaError, ValidationError, validate
from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError

from schema_generator import BaseInput, Metadata, get_schema

logging.basicConfig(format="HOOK(%(levelname)s): %(message)s")

ModulesList = dict[str, dict[str, Any] | None]


class Context(BaseModel):
    chezmoi: dict[str, Any]
    hosts: dict[str, ModulesList]
    metadata: Metadata | None = None


def get_context() -> Context:
    try:
        result = subprocess.run(
            ["chezmoi", "data", "--format=json"],
            capture_output=True,
            text=True,
            check=True,
        )
        context = result.stdout.strip()
        return Context.model_validate_json(context)

    except subprocess.CalledProcessError as e:
        logging.critical(
            f"Error fetching context, returned non-zero exit code {e.returncode}: {e.stderr.strip() if e.stderr else ''}"
        )
    except PydanticValidationError as e:
        logging.critical(f"Error fetching context, invalid json: {e}")

    exit(1)


class ModuleType(StrEnum):
    System = "system"
    User = "user"


class Module:
    type: ModuleType
    path: Path | None = None
    input_schema: dict
    input: BaseInput
    output: dict | None = None

    def __init__(self, name: str, source_dir: Path, data: BaseInput):
        module_type, _, module_rel_path = name.partition("/")
        path = source_dir.parent / module_type / module_rel_path

        self.type = ModuleType(module_type.lower())
        self.input = data

        if path.is_file() and os.access(path, os.X_OK):
            self.path = path
        else:
            if path.is_dir():
                for file in path.iterdir():
                    if file.name.startswith("default") and os.access(file, os.X_OK):
                        self.path = file
                        break
            if self.path is None:
                raise ValueError(f"Module `{name}` not found or not executable.")

        try:
            self.input_schema = json.loads(
                subprocess.run(
                    [str(self.path), "-s"], capture_output=True, text=True, check=True
                ).stdout.strip()
            )
        except subprocess.CalledProcessError as e:
            raise ValueError(
                f"Error fetching schema for module `{self.path}`, returned non-zero exit code {e.returncode}: {e.stderr.strip() if e.stderr else ''}"
            )

        try:
            validate(instance=self.input.model_dump(), schema=self.input_schema)
        except ValidationError as e:
            raise ValueError(f"Input validation error for module `{self.path}`: {e}")
        except SchemaError as e:
            raise ValueError(f"Schema error for module `{self.path}`: {e}")

    def generate(self):
        try:
            self.output = json.loads(
                subprocess.run(
                    [str(self.path), "-i", self.input.model_dump_json()],
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout.strip()
            )
        except subprocess.CalledProcessError as e:
            raise ValueError(
                f"Error running module `{self.path}`, returned non-zero exit code {e.returncode}: {e.stderr.strip() if e.stderr else ''}"
            )

        try:
            validate(instance=self.output, schema=get_schema())
        except ValidationError as e:
            raise ValueError(f"Output validation error for module `{self.path}`: {e}")
        except SchemaError as e:
            raise ValueError(f"Schema error for module `{self.path}`: {e}")

    def process(self, dry_run: bool):
        if dry_run:
            print(self.output)
        pass


def main() -> None:
    parser = ArgumentParser(
        prog="modules_hook",
        description="chezmoi pre run hook to generate dotfiles",
    )
    _ = parser.add_argument("-d", "--dry-run", action="store_true")
    args = parser.parse_args()
    dry_run = True if args.dry_run else False

    ctx = get_context()

    source_dir = ctx.chezmoi.get("sourceDir")
    if not isinstance(source_dir, str) or len(source_dir) == 0:
        logging.critical("No `sourceDir` found in chezmoi context.")
        exit(1)

    source_dir = Path(source_dir)
    if not source_dir.is_dir():
        logging.critical(
            f"Source directory `{source_dir}` does not exist or is not a directory."
        )
        exit(1)

    common = ctx.hosts.pop("common", None)
    if common is None:
        logging.critical("No `common` key in hosts context.")
        exit(1)

    hostname = ctx.chezmoi.get("hostname")
    if not isinstance(hostname, str) or len(hostname) == 0:
        logging.critical("No `hostname` found in chezmoi context.")
        exit(1)

    modules = ctx.hosts.get(hostname) or {}

    for name, global_data in common.items():
        if global_data is None:
            logging.warning(f"Common module `{name}` is set to null.")
            continue

        host_data = modules.get(name, "")

        if isinstance(host_data, str):
            modules[name] = global_data
            continue

        if host_data is None:
            _ = modules.pop(name, None)
            continue

        result = deepcopy(global_data)
        always_merger.merge(result, host_data)
        modules[name] = result

    for name, data in modules.items():
        if data is None:
            logging.warning(f"Module `{name}` is set to null.")
            continue

        module_input = BaseInput(
            chezmoi=ctx.chezmoi,
            metadata=ctx.metadata,
            data=data,
        )

        try:
            module = Module(name, source_dir, module_input)
            module.generate()
            module.process(dry_run)
        except ValueError as e:
            logging.error(e)

    return


if __name__ == "__main__":
    main()
