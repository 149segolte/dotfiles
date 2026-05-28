function fish_right_prompt --description 'Write out the right prompt'
    set -l normal (set_color --reset)

    # Show user/host only when connected via SSH
    set -l login_info
    if set -q SSH_CONNECTION; or set -q SSH_TTY; or set -q SSH_CLIENT
        set login_info "$USER""@"(prompt_hostname)
    end

    set -l duration_threshold 1000
    set -l duration_text
    if test -n "$CMD_DURATION"; and test $CMD_DURATION -gt $duration_threshold
        set -l secs (math --scale=1 $CMD_DURATION/1000 % 60)
        set -l mins (math --scale=0 $CMD_DURATION/60000 % 60)
        set -l hours (math --scale=0 $CMD_DURATION/3600000)

        set -l parts
        test $hours -gt 0; and set -a parts $hours"h"
        test $mins -gt 0; and set -a parts $mins"m"
        test $secs -gt 0; and set -a parts $secs"s"

        set duration_text (string join ' ' $parts)
    end

    set -l time_format %T
    set -l time_text (date +$time_format)

    set -l final_duration (set_color white) " "$duration_text $normal
    set -l final_remote (set_color $fish_color_host_remote) " "$login_info $normal
    set -l final_time (set_color white) " "$time_text $normal

    echo -n -s $final_duration $final_remote $final_time $normal
end
