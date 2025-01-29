#!/usr/bin/sh

if [ grep -q -s .local/bin/env "$HOME/.bashrc" ]; then
   echo ".bashrc is up to date"
   cat "$HOME/.bashrc"
   exit
fi

cat >> .bashrc <<EOF

. "$HOME/.local/bin/env"
EOF

echo "contents of $HOME/.bashrc"
cat "$HOME/.bashrc"
