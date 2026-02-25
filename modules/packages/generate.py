#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "jinja2>=3.1.6",
#     "pydantic>=2.12.5",
# ]
# ///
import json
import sys
from pathlib import Path
from typing import Annotated, Any, Literal, Union

from jinja2 import Environment, FileSystemLoader, select_autoescape
from pydantic import BaseModel, BeforeValidator, Field, ValidationError, field_validator

BASE_DIR = Path(__file__).parent.absolute()


def resource_path(v: str) -> str:
    res = ""
    try:
        res = (BASE_DIR / v).resolve(strict=True)
    except OSError:
        raise ValueError(f"Resource path {v} is not accessible")
    return str(res)


NonEmptyStr = Annotated[
    str, BeforeValidator(lambda x: str.strip(str(x))), Field(min_length=1)
]


class UpdateOptions(BaseModel):
    check: Union[bool, Literal["daily", "weekly"]] = False
    verify_installs: Union[bool, Literal["warn"]] = False


class HomebrewOptions(BaseModel):
    brews: list[NonEmptyStr] = []
    casks: list[NonEmptyStr] = []

    @field_validator("brews", "casks", mode="after")
    @classmethod
    def validate_entries(cls, entries: list[NonEmptyStr]) -> list[NonEmptyStr]:
        return sorted(set(entries))


class DNFOptions(BaseModel):
    clis: list[NonEmptyStr] = []

    @field_validator("clis", mode="after")
    @classmethod
    def validate_clis(cls, clis: list[NonEmptyStr]) -> list[NonEmptyStr]:
        return sorted(set(clis))


class InputData(BaseModel):
    updates: UpdateOptions = UpdateOptions()
    homebrew: HomebrewOptions | None = None
    dnf: DNFOptions | None = None


class ModuleInput(BaseModel):
    chezmoi: dict[str, Any]
    data: InputData


def main() -> None:
    try:
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

        scripts: list[dict[str, Any]] = []

        # Update handling
        if payload.data.updates.check:
            content_template = env.get_template("updates.jinja")

            run_modifiers = ["before"]
            if payload.data.updates.check in ["daily", "weekly"]:
                run_modifiers.append("onchange")

            scripts.append(
                {
                    "name": "packages-updates.sh.tmpl",
                    "run_modifiers": run_modifiers,
                    "contents": {
                        "kind": "inline",
                        "source": content_template.render(payload.data.model_dump()),
                    },
                }
            )

        # Package managers
        if payload.data.homebrew and (
            payload.data.homebrew.brews or payload.data.homebrew.casks
        ):
            content_template = env.get_template("homebrew.jinja")
            scripts.append(
                {
                    "name": "packages-homebrew.sh.tmpl",
                    "run_modifiers": ["onchange", "before"],
                    "contents": {
                        "kind": "inline",
                        "source": content_template.render(
                            payload.data.homebrew.model_dump()
                        ),
                    },
                }
            )

        if payload.data.dnf and payload.data.dnf.clis:
            content_template = env.get_template("dnf.jinja")
            scripts.append(
                {
                    "name": "packages-dnf.sh.tmpl",
                    "run_modifiers": ["onchange", "before"],
                    "contents": {
                        "kind": "inline",
                        "source": content_template.render(payload.data.model_dump()),
                    },
                }
            )

        output = {"scripts": scripts}
        print(json.dumps(output))

    except (ValidationError, ValueError) as e:
        print(f"Input validation error: {e}", file=sys.stderr)
        exit(1)


if __name__ == "__main__":
    main()
