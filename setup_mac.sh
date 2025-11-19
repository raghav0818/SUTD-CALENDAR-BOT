#!/bin/bash

# 1. Fix Directory: Switch to the folder where this script is located
cd "$(dirname "$0")"

echo "=================================================="
echo "  SUTD Calendar Bot - Dependency Installer"
echo "=================================================="
echo ""

# 2. Install
echo "Installing dependencies..."
pip3 install -r requirements.txt

echo ""
echo "[DONE] Installation attempt complete."
echo "You can now run the bot."