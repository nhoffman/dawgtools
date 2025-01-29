#!/usr/bin/sh

if [ grep -sq .local/bin/env "$HOME/.bashrc" ]; then
   echo ".bashrc is up to date"
   cat "$HOME/.bashrc"
   exit
fi

# cat >> .bashrc <<EOF

# . "$HOME/.local/bin/env"
# EOF
