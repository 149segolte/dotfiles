#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "email-validator>=2.3.0",
#     "pydantic>=2.12.5",
# ]
# ///
import contextlib
import json
import sys
from pathlib import Path
from typing import Annotated, Any, Literal, Union

from pydantic import (
    AfterValidator,
    BaseModel,
    BeforeValidator,
    EmailStr,
    Field,
    ValidationError,
)

BASE_DIR = Path(__file__).parent.absolute()


def relative_location(v: Path) -> Path:
    v = v.expanduser().resolve()
    if not v.is_relative_to(BASE_DIR):
        raise ValueError("value must be a relative path")
    return v.relative_to(BASE_DIR)


RelativePath = Annotated[Path, AfterValidator(relative_location)]

NonEmptyStr = Annotated[
    str, BeforeValidator(lambda x: str.strip(str(x))), Field(min_length=1)
]


class AllowedSigner(BaseModel):
    email: EmailStr
    keys: list[NonEmptyStr] = []


class AllowedSignerOptions(BaseModel):
    location: RelativePath
    entries: list[AllowedSigner] = []


class SignOptionsBase(BaseModel):
    pass


class SignOptionsSSH(SignOptionsBase):
    format: Literal["ssh"]
    key: RelativePath
    allowed_signers: AllowedSignerOptions | None = None


class SignOptionsOpenPGP(SignOptionsBase):
    format: Literal["openpgp"]
    key: NonEmptyStr


SignOptions = Annotated[
    Union[SignOptionsSSH, SignOptionsOpenPGP], Field(discriminator="format")
]


class GlobalExcludeOptions(BaseModel):
    location: RelativePath
    entries: list[NonEmptyStr] = []


class InputData(BaseModel):
    name: NonEmptyStr
    email: EmailStr
    sign: SignOptions | None = None
    global_exclude: GlobalExcludeOptions | None = None


class ModuleInput(BaseModel):
    chezmoi: dict[str, Any]
    data: InputData


def main() -> None:
    try:
        with contextlib.chdir(BASE_DIR):
            raw_input = sys.stdin.read()
            if not raw_input.strip():
                raise ValueError("No input provided on stdin")

            payload = ModuleInput.model_validate_json(raw_input, extra="forbid")
            chezmoi_dest_dir = (
                Path(payload.chezmoi.get("chezmoi", {}).get("destDir", "~"))
                .expanduser()
                .resolve()
            )
            files: list[dict[str, Any]] = []

            # Config file
            data = [
                "[init]",
                "    defaultbranch = main",
                "[user]",
                f"    name = {payload.data.name}",
                f"    email = {payload.data.email}",
            ]

            if payload.data.sign:
                data.extend(
                    [
                        f"    signingkey = {chezmoi_dest_dir / payload.data.sign.key}",
                        "[commit]",
                        "    gpgsign = true",
                        "[tag]",
                        "    gpgsign = true",
                        "[gpg]",
                        f"    format = {payload.data.sign.format}",
                    ]
                )

                if (
                    payload.data.sign.format == "ssh"
                    and payload.data.sign.allowed_signers
                ):
                    data.extend(
                        [
                            '[gpg "ssh"]',
                            f"    allowedsignersfile = {chezmoi_dest_dir / payload.data.sign.allowed_signers.location}",
                        ]
                    )

            if payload.data.global_exclude:
                data.extend(
                    [
                        "[core]",
                        f"    excludesfile = {chezmoi_dest_dir / payload.data.global_exclude.location}",
                    ]
                )

            files.append(
                {
                    "path": ".gitconfig",
                    "contents": {
                        "kind": "inline",
                        "source": "\n".join([s for s in data if s]) + "\n",
                    },
                }
            )

            # Allowed Signers File
            if payload.data.sign.format == "ssh" and payload.data.sign.allowed_signers:
                files.append(
                    {
                        "path": str(payload.data.sign.allowed_signers.location),
                        "contents": {
                            "kind": "inline",
                            "source": "\n".join(
                                [
                                    f'{e.email} namespaces="git" {key}'
                                    for e in payload.data.sign.allowed_signers.entries
                                    for key in e.keys
                                ]
                            )
                            + "\n",
                        },
                    }
                )

            # Global Excludes File
            if payload.data.global_exclude:
                files.append(
                    {
                        "path": str(payload.data.global_exclude.location),
                        "contents": {
                            "kind": "inline",
                            "source": "\n".join(payload.data.global_exclude.entries)
                            + "\n",
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
