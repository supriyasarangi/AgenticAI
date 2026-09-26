#!/bin/bash
# audit-log.sh: PostToolUse hook for Write/Edit
# Appends an audit line to docs/design/.audit-log after successful write/edit.
# Usage: audit-log.sh <tool-name> <file-path>
# Returns: 0 (always succeeds; logging failures are non-fatal)

TOOL_NAME="$1"
FILE_PATH="$2"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
HOSTNAME="${HOSTNAME:-$(hostname)}"
USER_ID="${USER:-unknown}"

# Ensure audit log directory exists
AUDIT_LOG_DIR="docs/design"
AUDIT_LOG="$AUDIT_LOG_DIR/.audit-log"

# Create the directory if it doesn't exist
mkdir -p "$AUDIT_LOG_DIR"

# Append an audit line
# Format: timestamp | tool | file | user | hostname
echo "$TIMESTAMP | $TOOL_NAME | $FILE_PATH | $USER_ID | $HOSTNAME" >> "$AUDIT_LOG" 2>/dev/null

# Log line added (or silently fail if permissions are wrong; non-fatal)
exit 0
