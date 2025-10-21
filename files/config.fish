if status is-interactive
    # Commands to run in interactive sessions can go here
    abbr -a -- cat 'bat --style=plain'
    abbr -a -- cd 'z'
    abbr -a -- grep 'rg'
    abbr -a -- ll 'eza -la'
    abbr -a -- ls 'eza'
end

# Global config
set -g fish_greeting

# Fisher includes (fzf, tide)
set -g tide_character_color $fish_color_operator
set -g tide_character_color_failure $fish_color_error
set -g tide_pwd_color_anchors $fish_color_command

# Zoxide
zoxide init fish | source

# Direnv
direnv hook fish | source
