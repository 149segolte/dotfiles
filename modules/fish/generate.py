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
from typing import Annotated, Any, Literal

from pydantic import BaseModel, BeforeValidator, Field, ValidationError, field_validator

BASE_DIR = Path(__file__).parent.absolute()

FISHER_SOURCE = "jorgebucaran/fisher"

DEFAULT_CONFIG = """\
# Default config
set -g fish_greeting
fish_add_path -m ~/.local/bin
"""


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


class ConfigOptions(BaseModel):
    override_default: bool = False
    content: NonEmptyStr | None = None
    abbreviations: dict[NonEmptyStr, NonEmptyStr] = {}
    manual_config: NonEmptyStr | None = None


class FisherOptions(BaseModel):
    update: bool = False
    plugins: list[NonEmptyStr] = []

    @field_validator("plugins", mode="after")
    def validate_plugins(cls, v: list[str]) -> list[str]:
        v = sorted(set(v))
        if FISHER_SOURCE in v:
            v.remove(FISHER_SOURCE)
        v.insert(0, FISHER_SOURCE)
        return v


class InputData(BaseModel):
    switch_shell: Literal["bash", "zsh"] | None = None
    config: ConfigOptions | None = None
    fisher: FisherOptions | None = None
    functions: dict[NonEmptyStr, NonEmptyStr] = {}


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

        # Switch shell configuration
        if payload.data.switch_shell:
            files.append(
                {
                    "path": ".bashrc"
                    if payload.data.switch_shell == "bash"
                    else ".zshrc",
                    "append": [
                        {
                            "kind": "local",
                            "source": resource_path(
                                f"switch_{payload.data.switch_shell}.sh"
                            ),
                        }
                    ],
                }
            )

        # Functions
        for func_name, func_body in payload.data.functions.items():
            files.append(
                {
                    "path": f".config/fish/functions/{func_name}.fish",
                    "contents": {
                        "kind": "inline",
                        "source": func_body.strip() + "\n",
                    },
                }
            )

        manual_config_content = [
            "function manual_config",
            "    echo 'Nothing to do.'",
            "end",
        ]
        if payload.data.config and payload.data.config.manual_config:
            manual_config_content[1] = payload.data.config.manual_config

        files.append(
            {
                "path": ".config/fish/functions/manual_config.fish",
                "contents": {
                    "kind": "inline",
                    "source": "\n".join(manual_config_content) + "\n",
                },
            }
        )

        if payload.data.fisher:
            files.append(
                {
                    "path": ".config/fish/functions/fisher_check.fish",
                    "contents": {
                        "kind": "local",
                        "source": resource_path("fisher_check.fish"),
                    },
                }
            )

        # Config file
        config_content = (
            []
            if (payload.data.config and payload.data.config.override_default)
            else [DEFAULT_CONFIG]
        )

        if payload.data.fisher:
            config_content.append(
                "# Fisher plugins check\n"
                f"fisher_check{' -u' if payload.data.fisher.update else ''} {' '.join([f'{x!r}' for x in payload.data.fisher.plugins])}"
            )

        if payload.data.config:
            if payload.data.config.content:
                config_content.append(f"# Host config\n{payload.data.config.content}")

            if len(payload.data.config.abbreviations) > 0:
                abbr_str = "# Abbreviations\nif status is-interactive\n"
                for abbr, exp in payload.data.config.abbreviations.items():
                    abbr_str += f"    abbr -a -- {abbr} {exp!r}\n"
                abbr_str += "end"
                config_content.append(abbr_str)

        config_content = [block.strip() for block in config_content if block.strip()]
        files.append(
            {
                "path": ".config/fish/config.fish",
                "contents": {
                    "kind": "inline",
                    "source": "\n\n".join(config_content) + "\n",
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
