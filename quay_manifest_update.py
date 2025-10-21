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
    mirror: str

    def exists(self, mirror: bool = False) -> bool:
        loc = self.upstream.split(":")[0]
        if mirror:
            loc = self.mirror

        print(f"Checking {'mirror' if mirror else 'upstream'}... ", end="")

        out = subprocess.run(["podman", "image", "search", loc], capture_output=True)
        if out.returncode != 0:
            print("not found.")
            return False

        lines = out.stdout.decode().splitlines()
        if len(lines) < 2 or not lines[1].strip().startswith(loc):
            print("not found (invalid output).")
            return False

        print("ok.")
        return True

    def fetch(self, platform: str, mirror: bool = False) -> str:
        loc = self.upstream
        if mirror:
            loc = f"{self.mirror}:{platform.split('/')[1]}"

        print("Fetching... ", end="")

        out = subprocess.run(
            ["podman", "image", "pull", f"--platform={platform}", loc],
            capture_output=True,
        )
        if out.returncode != 0:
            print("failed.")
            return ""

        lines = out.stdout.decode().splitlines()
        if len(lines) < 1:
            print("failed (invalid output).")
            return ""

        hash = lines[-1].strip()
        if len(hash) != 64:
            print("failed (invalid hash).")
            return ""

        print("ok.")
        return hash

    def push(self, platform: str) -> bool:
        loc = f"{self.mirror}:{platform.split('/')[1]}"

        print("Pushing... ", end="")

        out = subprocess.run(
            ["podman", "image", "tag", self.upstream, loc],
            capture_output=True,
        )
        if out.returncode != 0:
            print("failed (could not tag image).")
            return False

        lines = out.stdout.decode().splitlines()
        if len(lines) > 0:
            print("failed (tagging invalid output).")
            return False

        out = subprocess.run(
            ["podman", "image", "push", "--tls-verify=false", loc],
            capture_output=True,
        )
        if out.returncode != 0:
            print("failed (could not push image).")
            return False

        lines = out.stderr.decode().splitlines()
        if (
            len(lines) < 2
            or not lines[-1].strip() == "Writing manifest to image destination"
        ):
            print("failed (pushing invalid output).")
            return False

        print("ok.")
        return True

    def commit(self, tag: str, platforms: list[str]) -> bool:
        print("Updating manifest... ", end="")

        # TODO: check if necessary
        # Remove associated image
        out = subprocess.run(
            ["podman", "image", "rm", f"{self.mirror}:{tag}"],
            capture_output=True,
        )

        out = subprocess.run(
            ["podman", "manifest", "create", f"{self.mirror}:{tag}"],
            capture_output=True,
        )
        if out.returncode != 0:
            print("failed (could not create manifest).")
            return False

        for platform in platforms:
            loc = f"{self.mirror}:{platform.split('/')[1]}"
            out = subprocess.run(
                [
                    "podman",
                    "manifest",
                    "add",
                    f"{self.mirror}:{tag}",
                    f"docker://{loc}",
                ],
                capture_output=True,
            )
            if out.returncode != 0:
                print(f"failed (could not add {platform} to manifest).")
                return True

        out = subprocess.run(
            ["podman", "manifest", "push", "--all", f"{self.mirror}:{tag}"],
            capture_output=True,
        )
        if out.returncode != 0:
            print("failed (could not push manifest).")
            return True

        print("ok.")
        return True


parser = ArgumentParser(
    prog="quay_manifest_update.py", description="Update Quay manifests"
)
parser.add_argument(
    "tag", choices=["latest", "beta"], help="Push changes to the remote repository"
)
parser.add_argument(
    "--platform",
    default="linux/arm64,linux/amd64",
    help="Specify the platform(s) to build for",
)


def separator() -> None:
    print("-" * 40)


def main() -> None:
    args = parser.parse_args()
    platforms = args.platform.split(",")
    if len(platforms) == 0:
        print("No platforms specified.")
        return

    remotes = [
        Remote(
            name="alpine",
            upstream="docker.io/library/alpine:3.22",
            mirror="quay.io/149segolte/alpine",
        ),
        Remote(
            name="fedora",
            upstream="quay.io/fedora/fedora:42",
            mirror="quay.io/149segolte/fedora",
        ),
    ]

    print("Quay manifest update script")
    separator()
    print("Remotes: ", [r.name for r in remotes])

    for remote in remotes:
        print(f"\n--- {remote.name} ---")
        if not remote.exists():
            print("Skipping.")
            continue

        for platform in platforms:
            print(f"\nPlatform: {platform}")
            source_hash = remote.fetch(platform)
            if source_hash == "":
                print("Failed to fetch upstream image.")
                continue

            mirror_hash = ""
            if remote.exists(mirror=True):
                mirror_hash = remote.fetch(platform, mirror=True)

            if source_hash == mirror_hash:
                print(f"No update needed for {platform}.")
                continue

            remote.push(platform)

        print(f"\nManifest for: {platforms}")
        if remote.commit(args.tag, platforms):
            out = subprocess.run(
                ["podman", "manifest", "rm", f"{remote.mirror}:{args.tag}"],
            )
            if out.returncode != 0:
                print("Failed to remove manifest.")
                return


if __name__ == "__main__":
    main()
