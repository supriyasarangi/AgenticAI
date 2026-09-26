#!/bin/bash
# check-phi.sh: PreToolUse hook for Write/Edit
# Scans content for PHI-shaped patterns and blocks writes that match.
# Usage: check-phi.sh <file-path> <content>
# Returns: 0 if safe, non-zero if PHI-like pattern detected.

FILE_PATH="$1"
CONTENT="$2"

# Patterns to block (adjust as needed)
# SSN: 123-45-6789
SSN_PATTERN='[0-9]{3}-[0-9]{2}-[0-9]{4}'

# MRN-like: "MRN 12345678" or "Chart# 1234567" or "MR: 12345"
MRN_PATTERN='(MRN|Chart|MR)[#: ]+[0-9]{6,8}'

# DOB paired with a name/age: "John Doe, age 65, DOB 1959-03-15"
# (naive: DOB in YYYY-MM-DD or MM/DD/YYYY format)
DOB_PATTERN='(DOB|date.of.birth|born)[:\s]+(19|20)[0-9]{2}[-/]?(0[1-9]|1[0-2])[-/]?(0[1-9]|[12][0-9]|3[01])'

# Exclusions: allow patterns in the docs/design/ folder (this is the design doc, safe space)
if [[ "$FILE_PATH" =~ "docs/design/" ]]; then
    exit 0
fi

# Check for SSN pattern
if echo "$CONTENT" | grep -qE "$SSN_PATTERN"; then
    echo "🚫 PreToolUse BLOCK: SSN-like pattern detected in $FILE_PATH"
    echo "   This repo stores no real patient data. Use synthetic SSNs (e.g., '123-45-6789' only as an example)."
    exit 1
fi

# Check for MRN pattern
if echo "$CONTENT" | grep -qiE "$MRN_PATTERN"; then
    echo "🚫 PreToolUse BLOCK: MRN-like pattern detected in $FILE_PATH"
    echo "   Do not include real Medical Record Numbers. Use synthetic data (e.g., 'MRN 999999999')."
    exit 1
fi

# Check for DOB pattern
if echo "$CONTENT" | grep -qiE "$DOB_PATTERN"; then
    echo "🚫 PreToolUse BLOCK: DOB-like pattern detected in $FILE_PATH"
    echo "   Do not include real dates of birth. Use synthetic data (e.g., 'DOB 1960-01-01')."
    exit 1
fi

# Safe: no patterns matched
exit 0
