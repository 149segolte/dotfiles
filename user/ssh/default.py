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
from argparse import ArgumentParser
from pathlib import Path

from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError

BASE_DIR = Path(__file__).parent.absolute()

schema_location = BASE_DIR.parent.parent
sys.path.append(str(schema_location))
from schema_generator import (  # ty: ignore[unresolved-import]
    BaseInput,
    File,
    FileContents,
)
from schema_generator import Schema as Output  # ty: ignore[unresolved-import]


class InputData(BaseModel):
    keys: list[str] = []
    output_pubs: bool = False
    host_declarations: bool = False


class Input(BaseInput):
    data: InputData


def ssh_type_map(ssh_type: str) -> str:
    type_map = {
        "sk-ssh-ed25519@openssh.com": "ed25519_sk",
        "sk-ecdsa-sha2-nistp256@openssh.com": "ecdsa_sk",
        "ssh-rsa": "rsa",
        "ssh-ed25519": "ed25519",
        "ecdsa-sha2-nistp256": "ecdsa",
    }
    return type_map.get(ssh_type, ssh_type)


def main() -> None:
    parser = ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    _ = group.add_argument(
        "-s",
        "--schema",
        action="store_true",
        help="Output the input schema in JSON Schema format",
    )
    _ = group.add_argument("-i", "--input", help="Input data in JSON format")
    args = parser.parse_args()

    if args.schema:
        print(json.dumps(Input.model_json_schema()))
        return

    try:
        input = Input.model_validate_json(args.input)
        key_map = dict()

        for key in input.data.keys:
            key = key.strip()
            if not key:
                raise ValueError("Empty SSH key provided")

            parts = key.split()
            if len(parts) < 2:
                raise ValueError(f"Invalid SSH key format: {key}")

            key_type = ssh_type_map(parts[0])
            index = len([t for t in key_map.keys() if t.startswith(key_type)])
            if index > 0:
                key_map[f"{key_type}_alt_{index}"] = key
            else:
                key_map[key_type] = key

        files = list()

        # Public keys
        if input.data.output_pubs:
            files.extend(
                [
                    File(
                        path=f".ssh/id_{ty}.pub",
                        contents=FileContents(inline=key + "\n"),
                    )
                    for ty, key in key_map.items()
                ]
            )

        # Authorized keys
        files.append(
            File(
                path=".ssh/authorized_keys",
                contents=FileContents(inline="\n".join(key_map.values()) + "\n"),
            )
        )

        # Config
        files.append(
            File(
                path=".ssh/config",
                contents=FileContents(local=(BASE_DIR / "config").absolute()),
            )
        )

        # Config Hosts
        if input.data.host_declarations:
            files.append(
                File(
                    path=".ssh/config_hosts",
                    contents=FileContents(local=(BASE_DIR / "config_hosts").absolute()),
                )
            )

        output = Output(files=files)
        print(output.model_dump_json())

    except PydanticValidationError as e:
        print(f"Input validation error: {e}", file=sys.stderr)
        exit(1)
    except ValueError as e:
        print(f"Input validation error: {e}", file=sys.stderr)
        exit(1)


if __name__ == "__main__":
    main()
