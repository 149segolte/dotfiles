
# Switch to fish shell
if command -v fish >/dev/null 2>&1; then
    if [[ ( $PPID -eq 0 || $(ps --no-header --pid=$PPID --format=comm) != "fish" ) && -z ${BASH_EXECUTION_STRING} && ${SHLVL} == 1 && $- == *i* ]]
    then
        shopt -q login_shell && LOGIN_OPTION='--login' || LOGIN_OPTION=''
        exec fish $LOGIN_OPTION
    fi
fi
