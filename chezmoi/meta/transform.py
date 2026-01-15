#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "jinja2>=3.1.6",
# ]
# ///
import sys
from os import chdir, getcwd
from pathlib import Path
from subprocess import run

from jinja2 import Environment, FileSystemLoader, select_autoescape

SHOW_DIFF = True

MANAGE_TRANSFORMS = [
    ".chezmoidata.yaml",
    ".chezmoiscripts/run_once_install.sh.tmpl",
]


def log(msg: str, newline: bool = True) -> None:
    print(f"HOOK: {msg}", end="\n" if newline else "")


def main() -> None:
    working_dir = Path(sys.argv[1] if len(sys.argv) > 1 else getcwd())
    base_dir = working_dir / "meta"

    try:
        chdir(working_dir)
    except FileNotFoundError:
        log("Chezmoi source directory not found.")
    except PermissionError:
        log("Permission denied when accessing the source directory.")
    except OSError as e:
        print(f"An OS error occurred: {e}")

    # Check if files directory exists
    if not (base_dir / "files").is_dir():
        log("No templates directory found.")
        exit()

    env = Environment(
        loader=FileSystemLoader(base_dir / "files"),
        autoescape=select_autoescape(),
    )

    for file in MANAGE_TRANSFORMS:
        if not (base_dir / "files" / (file + ".j2")).is_file():
            log(f"Template for '{file}' not found, skipping.")
            continue

        template = env.get_template(file + ".j2")
        output = template.render()
        output_path = working_dir / file

        if output_path.exists():
            content = output_path.read_text(encoding="utf-8")
            if content == output:
                continue

            if SHOW_DIFF:
                diff_process = run(
                    ["diff", "-u", "--color=always", str(output_path), "-"],
                    input=output,
                    text=True,
                    capture_output=True,
                )
                if diff_process.stdout:
                    print(diff_process.stdout, flush=True)

            log(f"Changes detected in '{output_path}'", newline=False)
            overwrite = input(", overwrite (y/n): ")
            if overwrite.lower() != "y":
                log(f"Skipping update of '{output_path}'.")
                continue

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(output)
        log(f"Updated '{output_path}'.")


if __name__ == "__main__":
    main()
