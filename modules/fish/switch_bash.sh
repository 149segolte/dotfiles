# Switch to fish shell
if command -v fish >/dev/null 2>&1; then
    parent=$(ps -p $PPID -o comm= 2>/dev/null)

    # 1. Check parent is not fish (prevent loops)
    # 2. Check BASH_EXECUTION_STRING (ensure not running bash -c "...")
    # 3. Check SHLVL (ensure top level)
    # 4. Check interactive mode
    if [[ ( $PPID -eq 0 || "$parent" != "fish" ) && -z "${BASH_EXECUTION_STRING}" && ${SHLVL} == 1 && $- == *i* ]]; then
        if shopt -q login_shell; then
            LOGIN_OPTION='--login'
        else
            LOGIN_OPTION=''
        fi
        exec fish $LOGIN_OPTION
    fi
fi
