#!/bin/bash

JAKEYBOT_HOME=/jakeybot

# Test if /data/models.yaml and /data/text_models.yaml exist and symlink
# Only if it's readable for the current user
if [ -f /data/models.yaml ] && [ -r /data/models.yaml ]; then
    echo "[*] /data/models.yaml found, symlinking..."
    ln -frs /data/models.yaml $JAKEYBOT_HOME/data/models.yaml
    echo "[*] /data/models.yaml symlinked successfully."
else
    echo "[!] /data/models.yaml is not readable or does not exist. Using default models.yaml."
fi

# Same for text_models.yaml
if [ -f /data/text_models.yaml ] && [ -r /data/text_models.yaml ]; then
    echo "[*] /data/text_models.yaml found, symlinking..."
    ln -frs /data/text_models.yaml $JAKEYBOT_HOME/data/text_models.yaml
    echo "[*] /data/text_models.yaml symlinked successfully."
else
    echo "[!] /data/text_models.yaml is not readable or does not exist. Using default text_models.yaml."
fi

# Run the main application
python3 main.py