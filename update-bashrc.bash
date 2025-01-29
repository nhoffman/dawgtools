#!/usr/bin/bash

if grep -q -s .local/bin/env "$HOME/.bashrc"; then
   echo "$HOME/.bashrc is up to date"
   exit
fi

cat >> "$HOME/.bashrc" <<EOF

. "\$HOME/.local/bin/env"
EOF

echo "updated $HOME/.bashrc"
