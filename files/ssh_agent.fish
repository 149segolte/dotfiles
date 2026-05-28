# SSH Agent
set -e SSH_AUTH_SOCK
ssh-agent -uu > /dev/null 2>&1 # This cleans up slate sockets

# Find previous agents (ones without leading slash)
set -l prev_agent_pid (ps -xo pid=,comm= | rg "[^/]ssh-agent" | awk '{print $1}' | head -n 1)

if test -n "$prev_agent_pid"
    # Find associated unix socket
    set -l prev_agent_sock (lsof -p $prev_agent_pid -a -U -Fn 2>/dev/null | string match -er '^n' | string replace 'n' '')

    if test -S "$prev_agent_sock"
        set -gx SSH_AUTH_SOCK $prev_agent_sock
        set -gx SSH_AGENT_PID $prev_agent_pid
    end
end

if not set -q SSH_AUTH_SOCK; or not test -S "$SSH_AUTH_SOCK"
    eval (ssh-agent -c)
end
