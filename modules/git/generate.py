#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "email-validator>=2.3.0",
#     "jinja2>=3.1.6",
#     "pydantic>=2.12.5",
# ]
# ///
import contextlib
import json
import sys
from pathlib import Path
from typing import Annotated, Any, Literal, Union

from jinja2 import Environment, FileSystemLoader, select_autoescape
from pydantic import (
    AfterValidator,
    BaseModel,
    BeforeValidator,
    EmailStr,
    Field,
    FieldSerializationInfo,
    SerializerFunctionWrapHandler,
    ValidationError,
    WrapSerializer,
    field_validator,
)

BASE_DIR = Path(__file__).parent.absolute()


def relative_location(v: Path) -> Path:
    v = v.expanduser().resolve()
    if not v.is_relative_to(BASE_DIR):
        raise ValueError("value must be a relative path")
    return v.relative_to(BASE_DIR)


def serialize_relative_path(
    v: Any, handler: SerializerFunctionWrapHandler, info: FieldSerializationInfo
) -> str:
    v = handler(v)
    if not isinstance(v, Path):
        raise ValueError("value must be a Path")

    if isinstance(info.context, dict):
        base_dir = info.context.get("base_dir", Path("~"))
        v = base_dir / v

    return str(v)


RelativePath = Annotated[
    Path, AfterValidator(relative_location), WrapSerializer(serialize_relative_path)
]

NonEmptyStr = Annotated[
    str, BeforeValidator(lambda x: str.strip(str(x))), Field(min_length=1)
]


class AllowedSigner(BaseModel):
    email: EmailStr
    keys: list[NonEmptyStr] = []

    @field_validator("keys", mode="after")
    @classmethod
    def validate_keys(cls, keys: list[NonEmptyStr]) -> list[NonEmptyStr]:
        keys = sorted(set(keys))
        for key in keys:
            parts = key.split()
            if len(parts) < 2:
                raise ValueError(f"Invalid SSH key format: {key}")
        return keys

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, AllowedSigner):
            return NotImplemented
        return self.email == other.email

    def __hash__(self) -> int:
        return self.email.__hash__()


class AllowedSignerOptions(BaseModel):
    location: RelativePath
    entries: list[AllowedSigner] = []

    @field_validator("entries", mode="after")
    @classmethod
    def validate_entries(cls, entries: list[AllowedSigner]) -> list[AllowedSigner]:
        return sorted(set(entries), key=lambda e: e.email)


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

    @field_validator("entries", mode="after")
    @classmethod
    def validate_entries(cls, entries: list[NonEmptyStr]) -> list[NonEmptyStr]:
        return sorted(set(entries))


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

            env = Environment(
                loader=FileSystemLoader(BASE_DIR),
                autoescape=select_autoescape(),
                trim_blocks=True,
                lstrip_blocks=True,
            )
            chezmoi_dest_dir = (
                Path(payload.chezmoi.get("chezmoi", {}).get("destDir", "~"))
                .expanduser()
                .resolve()
            )

            files: list[dict[str, Any]] = []

            # Config file
            config_template = env.get_template("gitconfig.jinja")
            files.append(
                {
                    "path": ".gitconfig",
                    "contents": {
                        "kind": "inline",
                        "source": config_template.render(
                            payload.data.model_dump(
                                context={"base_dir": chezmoi_dest_dir}
                            )
                        ),
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
