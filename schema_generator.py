#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "pydantic>=2.12.5",
# ]
# ///
import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, model_validator


class Metadata(BaseModel):
    pass


class BaseInput(BaseModel):
    chezmoi: dict[str, Any]
    metadata: Metadata | None = None
    data: dict[str, Any]


class FileContents(BaseModel):
    local: Path | None = None
    inline: str | None = None

    @model_validator(mode="after")
    def check_mutually_exclusive_content(self) -> FileContents:
        set_values = self.model_dump(exclude_unset=True, exclude_none=True).values()
        if len(set_values) > 1:
            raise ValueError("Fields 'inline' and 'local' are mutually exclusive.")
        return self


class File(BaseModel):
    path: str
    overwrite: bool | None = False
    contents: FileContents | None = None
    mode: int | None = None
    pass


class Schema(BaseModel):
    files: list[File] | None = None


def get_schema() -> dict[str, Any]:
    return Schema.model_json_schema()


if __name__ == "__main__":
    print(json.dumps(get_schema()))
