#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "pydantic>=2.12.5",
# ]
# ///
import json
import sys
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field
from pydantic import ValidationError as PydanticValidationError

BASE_DIR = Path(__file__).parent.absolute()


class InputData(BaseModel):
    keys: list[str] = Field(default=[])
    output_pubs: bool = Field(default=False)
    host_declarations: bool = Field(default=False)


class ModuleInput(BaseModel):
    chezmoi: dict[str, Any]
    data: InputData


def ssh_type_map(ssh_type: str) -> str | None:
    type_map = {
        "sk-ssh-ed25519@openssh.com": "ed25519_sk",
        "sk-ecdsa-sha2-nistp256@openssh.com": "ecdsa_sk",
        "ssh-rsa": "rsa",
        "ssh-ed25519": "ed25519",
        "ecdsa-sha2-nistp256": "ecdsa",
    }
    return type_map.get(ssh_type)


def main() -> None:
    try:
        raw_input = sys.stdin.read()
        if not raw_input.strip():
            raise ValueError("No input provided on stdin")

        payload = ModuleInput.model_validate_json(raw_input)
        key_map: dict[str, list[str]] = {}

        for key in payload.data.keys:
            key = key.strip()
            if not key:
                raise ValueError("Empty SSH key provided")

            parts = key.split()
            if len(parts) < 2:
                raise ValueError(f"Invalid SSH key format: {key}")

            key_type = ssh_type_map(parts[0])
            if key_type is None:
                raise ValueError(f"Unsupported SSH key type: {key_type}")

            key_map.setdefault(key_type, []).append(key)

        keys = {
            key_type if idx == 0 else f"{key_type}_alt{idx}": key
            for key_type, keys in key_map.items()
            for idx, key in enumerate(keys)
        }

        files: list[dict[str, Any]] = []

        # Public keys
        if payload.data.output_pubs:
            files.extend(
                [
                    {
                        "path": f".ssh/id_{name}.pub",
                        "contents": {"inline": key + "\n"},
                    }
                    for name, key in keys.items()
                ]
            )

        # Authorized keys
        files.append(
            {
                "path": ".ssh/authorized_keys",
                "contents": {"inline": "\n".join(keys.values()) + "\n"},
            }
        )

        # Config
        files.append(
            {
                "path": ".ssh/config",
                "contents": {"local": str((BASE_DIR / "config").absolute())},
            }
        )

        # Config Hosts
        if payload.data.host_declarations:
            files.append(
                {
                    "path": ".ssh/config_hosts",
                    "contents": {"local": str((BASE_DIR / "config_hosts").absolute())},
                }
            )

        output = {"files": files}
        print(json.dumps(output))

    except (PydanticValidationError, ValueError) as e:
        print(f"Input validation error: {e}", file=sys.stderr)
        exit(1)


if __name__ == "__main__":
    main()
