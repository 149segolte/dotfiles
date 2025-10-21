#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///
from dataclasses import dataclass
from argparse import ArgumentParser
import subprocess


@dataclass
class Remote:
    name: str
    upstream: str
    tag: str
    mirror: str

    def exists(self, mirror: bool = False) -> bool:
        loc = self.upstream
        if mirror:
            loc = self.mirror

        print(f"Checking {'mirror' if mirror else 'upstream'}... ", end="")

        out = subprocess.run(["podman", "image", "search", loc], capture_output=True)
        if out.returncode != 0:
            print("not found.")
            return False

        lines = out.stdout.decode().splitlines()
        if len(lines) > 1 and lines[1].strip().startswith(loc):
            print("ok.")
            return True

        print("not found.")
        return False

    def fetch(self, mirror: str = "") -> str:
        loc = f"{self.upstream}:{self.tag}"
        if mirror != "":
            loc = f"{self.mirror}:{mirror}"

        print("Fetching... ", end="")

        out = subprocess.run(["podman", "image", "pull", loc], capture_output=True)
        if out.returncode != 0:
            print("failed.")
            return ""

        lines = out.stdout.decode().splitlines()
        if len(lines) > 0:
            hash = lines[-1].strip()
            if len(hash) == 64:
                print("ok.")
                return hash

        print("failed.")
        return ""

    def push(self, mirror: str) -> None:
        loc = f"{self.mirror}:{mirror}"
        print("Pushing... ", end="")

        out = subprocess.run(
            ["podman", "image", "tag", f"{self.upstream}:{self.tag}", loc],
            capture_output=True,
        )
        if out.returncode != 0:
            print("failed (could not tag image).")
            return

        lines = out.stdout.decode().splitlines()
        if len(lines) > 0:
            print("failed (tagging invalid output).")

        out = subprocess.run(
            ["podman", "image", "push", "--tls-verify=false", loc],
            capture_output=True,
        )
        if out.returncode != 0:
            print("failed (could not push image).")
            return

        lines = out.stderr.decode().splitlines()
        if (
            len(lines) > 1
            and lines[-1].strip() == "Writing manifest to image destination"
        ):
            print("ok.")
            return

        print("failed.")
        return


remotes = [
    Remote(
        name="alpine",
        upstream="docker.io/library/alpine",
        tag="3.22",
        mirror="quay.io/149segolte/alpine",
    ),
    Remote(
        name="fedora",
        upstream="quay.io/fedora/fedora",
        tag="42",
        mirror="quay.io/149segolte/fedora",
    ),
]


parser = ArgumentParser(
    prog="quay_manifest_update.py", description="Update Quay manifests"
)
parser.add_argument(
    "push", choices=["latest", "beta"], help="Push changes to the remote repository"
)


def separator() -> None:
    print("-" * 40)


def main() -> None:
    args = parser.parse_args()
    print("Quay manifest update script")
    separator()
    print("Remotes: ", [r.name for r in remotes])

    for remote in remotes:
        print(f"\n--- {remote.name} ---")
        if not remote.exists():
            print("Skipping.")
            continue

        source_hash = remote.fetch()
        if source_hash == "":
            print("Failed to fetch upstream image.")
            continue

        mirror_hash = ""
        if remote.exists(mirror=args.push):
            mirror_hash = remote.fetch(mirror=args.push)

        if source_hash == mirror_hash:
            print("No update needed.")
            continue

        remote.push(args.push)


if __name__ == "__main__":
    main()
