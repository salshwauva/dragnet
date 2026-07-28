#!/usr/bin/env bash
# Install the dragnet launchd plist into ~/Library/LaunchAgents.
# Idempotent: unloads any existing version before loading the new one.

set -euo pipefail

REPO_PATH="$(cd "$(dirname "$0")/.." && pwd)"
PLIST_SRC="$REPO_PATH/com.dragnet.scraper.plist"
PLIST_DST="$HOME/Library/LaunchAgents/com.dragnet.scraper.plist"

if [[ ! -f "$PLIST_SRC" ]]; then
    echo "error: $PLIST_SRC not found"
    exit 1
fi

# Substitute the repo path into the template and write to the target.
mkdir -p "$HOME/Library/LaunchAgents"
sed "s|{{REPO_PATH}}|$REPO_PATH|g" "$PLIST_SRC" > "$PLIST_DST"
echo "wrote $PLIST_DST"

# Unload existing instance if loaded (ignore errors).
launchctl unload "$PLIST_DST" 2>/dev/null || true

# Load the new plist.
launchctl load "$PLIST_DST"
echo "loaded com.dragnet.scraper"

# Verify.
if launchctl list | grep -q com.dragnet.scraper; then
    echo "ok: com.dragnet.scraper is registered"
    echo
    echo "next run: 07:30 or 17:30 local, whichever comes first"
    echo "logs: $REPO_PATH/dragnet.log  (and dragnet.err for errors)"
    echo
    echo "to trigger a manual run: source .venv/bin/activate && python -m dragnet"
    echo "to unload: launchctl unload $PLIST_DST"
else
    echo "warning: launchctl list does not show com.dragnet.scraper"
    exit 1
fi
