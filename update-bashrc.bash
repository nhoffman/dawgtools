#!/usr/bin/bash

if grep -q -s .local/bin/env "$HOME/.bashrc"; then
    echo "$HOME/.bashrc already sources \$HOME/.local/bin/env"
else
    cat >> "$HOME/.bashrc" <<EOF

. "\$HOME/.local/bin/env"
EOF
fi

if grep -q -s XDG "$HOME/.bashrc"; then
    echo "XDG variables are already configured"
else
    cat >> "$HOME/.bashrc" <<EOF
export XDG_BIN_HOME="\${XDG_BIN_HOME:-\$HOME/.local/bin}"
export XDG_CACHE_HOME="\${XDG_CACHE_HOME:-\$HOME/.cache}"
export XDG_CONFIG_HOME="\${XDG_CONFIG_HOME:-\$HOME/.config}"
export XDG_DATA_HOME="\${XDG_DATA_HOME:-\$HOME/.local/share}"
EOF
fi



