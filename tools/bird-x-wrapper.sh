#!/bin/bash
# =================================================
# Bird-X: Secure Wrapper for Twitter CLI (bird)
# =================================================
# This script loads credentials from ../secrets.json
# and executes the 'bird' command.

# Resolve the directory of this script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ROOT_DIR="$(dirname "$DIR")"
SECRETS_FILE="$ROOT_DIR/secrets.json"

# Check if secrets.json exists
if [ ! -f "$SECRETS_FILE" ]; then
    echo "Error: secrets.json not found at $SECRETS_FILE"
    echo "Please copy docs/secrets.json.example to secrets.json and fill in your Twitter tokens."
    exit 1
fi

# Extract tokens using python (to avoid jq dependency if possible, or simple grep)
# Using simple grep/sed for portability. Assumes strict JSON format "key": "value"
AUTH_TOKEN=$(grep -oP '"twitter_auth_token":\s*"\K[^"]+' "$SECRETS_FILE")
CT0=$(grep -oP '"twitter_ct0":\s*"\K[^"]+' "$SECRETS_FILE")

if [ -z "$AUTH_TOKEN" ] || [ -z "$CT0" ]; then
    echo "Error: Could not extract twitter_auth_token or twitter_ct0 from secrets.json"
    exit 1
fi

# Export variables for the bird process
export AUTH_TOKEN="$AUTH_TOKEN"
export CT0="$CT0"

# Check if 'bird' is in PATH, if not try common locations or local install
BIRD_CMD="bird"
if ! command -v bird &> /dev/null; then
    # Try local node_modules if user installed it locally
    if [ -f "$ROOT_DIR/node_modules/.bin/bird" ]; then
        BIRD_CMD="$ROOT_DIR/node_modules/.bin/bird"
    else
        echo "Error: 'bird' command not found. Please install it with 'npm install -g @steipete/bird'."
        exit 1
    fi
fi

# Execute bird with arguments
exec "$BIRD_CMD" "$@"
