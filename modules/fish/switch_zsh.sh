# Switch to fish shell
if command -v fish >/dev/null 2>&1; then
    parent=$(ps -p $PPID -o comm= 2>/dev/null)

    # 1. Check parent is not fish (prevent loops)
    # 2. Check ZSH_EXECUTION_STRING (ensure not running zsh -c "...")
    # 3. Check SHLVL (ensure top level)
    # 4. Check interactive mode
    if [[ ( $PPID -eq 0 || "$parent" != "fish" ) && -z ${ZSH_EXECUTION_STRING} && ${SHLVL} == 1 && -o interactive ]]; then
        if [[ -o login ]]; then
            LOGIN_OPTION='--login'
        else
            LOGIN_OPTION=''
        fi
        exec fish $LOGIN_OPTION
    fi
fi
