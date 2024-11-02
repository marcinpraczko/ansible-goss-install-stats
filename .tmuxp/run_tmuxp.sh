#!/usr/bin/env bash

# Resolve the absolute path to the actual script
SCRIPT_PATH=$(readlink -f "$0")
SCRIPT_DIR=$(dirname "${SCRIPT_PATH}")

# Set the project root to the script's directory if not already set
MPOSL_PROJECT_ROOT="${MPOSL_PROJECT_ROOT:-${SCRIPT_DIR}}"
export MPOSL_PROJECT_ROOT

# Load the tmuxp configuration
tmuxp load -y "${MPOSL_PROJECT_ROOT}/main.yaml"
