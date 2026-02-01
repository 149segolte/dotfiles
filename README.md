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

## Modules

Modules serve as extendable format outside of chezmoi's dependence on `text/template` from go. They can be any form of executable (binaries, scripts, etc) with the interface:

```
module -s/--schema => json schema for module context
module -i/--input <context> => `stdout` json following `schema.json`
```

Modules are queried inside:

- `system/`: Contains system configuration that needs to be defined in terms of absolute paths.
- `user/`: Contains user configuration that is relative to the home directory.
