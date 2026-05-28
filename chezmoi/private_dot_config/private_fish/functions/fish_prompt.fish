# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

function fish_prompt --description 'Write out the prompt'
    set -l last_pipestatus $pipestatus
    set -lx __fish_last_status $status # Export for __fish_print_pipestatus.
    set -l normal (set_color --reset)

    set -l delimiter "|"
    set -l prompt_status "["
    set -l status_failed 0
    for code in $last_pipestatus
        if not contains $code 0 141
            set status_failed 1
        end
        set prompt_status "$prompt_status$code$delimiter"
    end

    # Print pipestatus on any non-zero code in the pipeline
    if test $status_failed -eq 0
        set -e prompt_status
    else
        set prompt_status (string trim -c $delimiter $prompt_status)"]"
    end

    # Color the prompt differently when we're root
    set -l color_cwd $fish_color_cwd
    set -l suffix '❯'
    if functions -q fish_is_root_user; and fish_is_root_user
        if set -q fish_color_cwd_root
            set color_cwd $fish_color_cwd_root
        end
        set suffix '#'
    end

    # Prompt character color changes on any non-zero in the pipeline
    set -l char_color "blue"
    if test $status_failed -eq 1
        set char_color $fish_color_error
    end

    set -l final_cwd (set_color $color_cwd) (prompt_pwd) $normal
    set -l final_vcs (fish_vcs_prompt) $normal
    set -l final_status (set_color $fish_color_status) " "$prompt_status $normal
    set -l final_char (set_color $char_color) " "$suffix $normal

    echo -n -s $final_cwd $final_vcs $final_status $final_char ' ' $normal
end
