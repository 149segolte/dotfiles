# Fisher plugins check
function fisher_check
    argparse u/update -- $argv
    or return 2

    if not status is-interactive
        return 1
    end

    if not type -q fisher
        curl -sL https://raw.githubusercontent.com/jorgebucaran/fisher/main/functions/fisher.fish | source
    end

    set -l current (fisher list)

    for plugin in $argv
        if string match -q $plugin $current
            if set -ql _flag_update
                fisher update $plugin
            end
        else
            fisher install $plugin
        end
    end
end
