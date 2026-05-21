# dotfiles

Personal dotfiles management across different machines using `chezmoi`.

## Usage

Requires `chezmoi` and `uv` to be available on the system.

Initialize the config using:

```sh
chezmoi init https://github.com/149segolte/dotfiles.git
```

Check changes using:

```sh
chezmoi diff # or
chezmoi -nv apply
```

Apply changes using:

```sh
chezmoi -v apply
```
