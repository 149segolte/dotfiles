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
from typing import Annotated, Any

from pydantic import BaseModel, BeforeValidator, Field, ValidationError, field_validator

BASE_DIR = Path(__file__).parent.absolute()

SSH_KEY_TYPES = {
    "sk-ssh-ed25519@openssh.com": "ed25519_sk",
    "sk-ecdsa-sha2-nistp256@openssh.com": "ecdsa_sk",
    "ssh-rsa": "rsa",
    "ssh-ed25519": "ed25519",
    "ecdsa-sha2-nistp256": "ecdsa",
}

NonEmptyStr = Annotated[
    str, BeforeValidator(lambda x: str.strip(str(x))), Field(min_length=1)
]


class InputData(BaseModel):
    keys: set[NonEmptyStr] = set()
    output_pubs: bool = False

    @field_validator("keys", mode="after")
    @classmethod
    def validate_keys(cls, keys: set[NonEmptyStr]) -> set[NonEmptyStr]:
        for key in keys:
            parts = key.split()
            if len(parts) < 2:
                raise ValueError(f"Invalid SSH key format: {key}")

            key_type = SSH_KEY_TYPES.get(parts[0])
            if key_type is None:
                raise ValueError(f"Unsupported SSH key type: {parts[0]}")

        return keys


class ModuleInput(BaseModel):
    chezmoi: dict[str, Any]
    data: InputData


def main() -> None:
    try:
        raw_input = sys.stdin.read()
        if not raw_input.strip():
            raise ValueError("No input provided on stdin")

        payload = ModuleInput.model_validate_json(raw_input, extra="forbid")
        files: list[dict[str, Any]] = []

        # Public keys
        if payload.data.output_pubs:
            counter = {k: 0 for k in SSH_KEY_TYPES.values()}
            keys = {}

            for key in payload.data.keys:
                parts = key.split()
                key_type = SSH_KEY_TYPES.get(parts[0], "")
                count = counter[key_type]
                keys[key_type if count == 0 else f"{key_type}_alt{count}"] = key
                counter[key_type] += 1

            files.extend(
                [
                    {
                        "path": f".ssh/id_{name}.pub",
                        "contents": {"kind": "inline", "source": key + "\n"},
                    }
                    for name, key in keys.items()
                ]
            )

        # Authorized keys
        files.append(
            {
                "path": ".ssh/authorized_keys",
                "contents": {
                    "kind": "inline",
                    "source": "\n".join(payload.data.keys) + "\n",
                },
            }
        )

        # Config
        files.append(
            {
                "path": ".ssh/config",
                "contents": {
                    "kind": "local",
                    "source": str((BASE_DIR / "config").absolute()),
                },
            }
        )

        output = {"files": files}
        print(json.dumps(output))

    except (ValidationError, ValueError) as e:
        print(f"Input validation error: {e}", file=sys.stderr)
        exit(1)


if __name__ == "__main__":
    main()
