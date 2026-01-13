# Fisher Plugins
fisher_check "jorgebucaran/fisher" "patrickf1/fzf.fish" "ilancosman/tide@v6"

# Global config
set -g fish_greeting
set -g EDITOR nvim

if status is-interactive
    # Commands to run in interactive sessions can go here
    abbr -a -- cat 'bat --style=plain'
    abbr -a -- cd 'z'
    abbr -a -- grep 'rg'
    abbr -a -- ll 'eza -la'
    abbr -a -- ls 'eza'
end

# Zoxide
zoxide init fish | source

