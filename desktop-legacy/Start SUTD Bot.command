#!/bin/bash
# ============================================================
#  SUTD Calendar Bot - just double-click this file.
#  No code editor needed. Sets itself up the first time.
#  (First time only: right-click -> Open, to get past Gatekeeper.)
# ============================================================
cd "$(dirname "$0")" || exit 1

if ! command -v python3 >/dev/null 2>&1; then
  echo
  echo "  Python is not installed on this Mac."
  echo
  echo "  I'm opening the download page for you now."
  echo "  Install it, then double-click this file again."
  echo
  open https://www.python.org/downloads/
  read -r -p "Press Enter to close..."
  exit 1
fi

if [ ! -x ".venv/bin/python" ]; then
  echo
  echo "  First-time setup. This takes a minute, only happens once."
  echo
  if ! python3 -m venv .venv \
     || ! .venv/bin/python -m pip install --upgrade pip --quiet \
     || ! .venv/bin/python -m pip install -r requirements.txt --quiet; then
    echo
    echo "  Setup failed - most likely no internet connection."
    echo "  Connect to wifi and double-click this file again."
    echo
    read -r -p "Press Enter to close..."
    exit 1
  fi
  echo "  Setup done."
  echo
fi

if ! .venv/bin/python sutd_calendar_bot.py; then
  echo
  echo "  The bot stopped with an error. Details are in sutd_bot.log"
  echo "  If this keeps happening, delete the '.venv' folder and run this again."
  echo
  read -r -p "Press Enter to close..."
fi
