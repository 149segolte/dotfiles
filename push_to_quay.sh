#!/usr/bin/env bash
podman image rm quay.io/149segolte/dotfiles:latest
podman manifest rm quay.io/149segolte/dotfiles:latest
podman manifest create quay.io/149segolte/dotfiles:latest
podman build --jobs=2 --platform=linux/arm64,linux/amd64 --manifest quay.io/149segolte/dotfiles:latest .
podman manifest push --all quay.io/149segolte/dotfiles:latest
podman manifest rm quay.io/149segolte/dotfiles:latest