# .claude/ — Claude Code Configuration

This directory contains Claude Code-specific configuration for the Banner Health project.

## Overview

- **`settings.json`** — Hooks configuration (PreToolUse, PostToolUse)
- **`hooks/`** — Hook scripts (PHI guard, audit logging)
- **`skills/banner-health/`** — Clinical workflow skill (invocable as `/banner-health`)

## Hooks

### PreToolUse: PHI Guard (`check-phi.sh`)

**When**: Before any Write or Edit tool call  
**What it does**: Scans content for PHI-shaped patterns (SSN, MRN, DOB) and blocks the write if found

**Blocked patterns**:
- SSN: `123-45-6789` (format: `\d{3}-\d{2}-\d{4}`)
- MRN: `MRN 12345678` or `Chart# 1234567` (format: `(MRN|Chart|MR)[#: ]+\d{6,8}`)
- DOB: `DOB 1960-01-15` (format: date in YYYY-MM-DD or MM/DD/YYYY)

**If blocked**:
```
🚫 PreToolUse BLOCK: SSN-like pattern detected in [file]
   This repo stores no real patient data. Use synthetic SSNs (e.g., '123-45-6789' only as an example).
```

Replace real data with synthetic equivalents and retry.

### PostToolUse: Audit Logging (`audit-log.sh`)

**When**: After any successful Write or Edit tool call  
**What it does**: Appends a log line to `docs/design/.audit-log`

**Log format**:
```
2026-09-26T06:42:35Z | Write | test-file.md | labuser | ubuntu
```

Fields: `timestamp | tool_name | file_path | user_id | hostname`

**View audit log**:
```bash
tail -20 docs/design/.audit-log
```

## Skills

### /banner-health

**Location**: `.claude/skills/banner-health/SKILL.md`

**Commands**:
```bash
/banner-health draft <visit-input>
/banner-health summarize <patient-context>
```

**Examples**:
```bash
/banner-health draft "Chief complaint: SOB × 3 days. Exam: diminished breath sounds, bilateral."

/banner-health summarize "PMH: HTN, DM2. Meds: Lisinopril, Metoprolol. Recent: ED visit 09/18, troponin negative."
```

See `.claude/skills/banner-health/SKILL.md` for full documentation.

## Configuration Files

### settings.json

Defines PreToolUse and PostToolUse hooks. Structure:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/check-phi.sh \"${file_path}\" \"${content}\"",
            "timeout": 5
          }
        ]
      }
    ],
    "PostToolUse": [...]
  }
}
```

**To modify hooks**:
1. Edit `.claude/settings.json` (JSON must remain valid)
2. Restart Claude Code for changes to take effect
3. Test the hook: try a Write/Edit that should trigger it

**To disable a hook temporarily**:
- Comment out the matcher in the PreToolUse/PostToolUse array, or
- Use `/config` in Claude Code to adjust settings

### .claude.local.md (Optional)

For personal/local overrides. If you create a `.claude.local.md` in this project, it will be loaded alongside root `CLAUDE.md` and can override specific settings for your local development environment.

## Testing Hooks

### Test PHI Block (PreToolUse)

```bash
# Should be blocked (SSN pattern)
bash .claude/hooks/check-phi.sh "test.md" "SSN: 123-45-6789"

# Should be blocked (MRN pattern)
bash .claude/hooks/check-phi.sh "test.md" "MRN 12345678"

# Should be allowed (clean)
bash .claude/hooks/check-phi.sh "test.md" "Patient A, age 65, synthetic data"
```

Exit code 0 = allowed, non-zero = blocked.

### Test Audit Logging (PostToolUse)

```bash
bash .claude/hooks/audit-log.sh "Write" "my-file.md"
tail docs/design/.audit-log  # Should show the new entry
```

## Troubleshooting

### Hook not triggering?

1. Confirm `settings.json` is valid JSON: `python3 -m json.tool .claude/settings.json`
2. Confirm hook scripts are executable: `ls -la .claude/hooks/`
3. Restart Claude Code and retry
4. Check Claude Code logs for hook errors

### Hook blocking legitimate writes?

The PHI patterns may have false positives. Options:

1. **Bypass for a specific file**: Edit the hook script to add file exclusions (e.g., `if [[ "$FILE_PATH" =~ "docs/" ]]; then exit 0; fi`)
2. **Refine the regex**: Edit the pattern in `check-phi.sh` (but be careful — tighter patterns = more false negatives)
3. **Disable the hook**: Comment out the PreToolUse block in `settings.json` (not recommended for production, but OK for testing)

### Audit log not being written?

1. Confirm `docs/design/` directory exists (it should — created during setup)
2. Confirm write permissions: `ls -la docs/design/.audit-log`
3. Check if the PostToolUse hook errored (non-fatal, but still logged somewhere)

## For Contributors

When working in this repo:

1. **Read root `CLAUDE.md`** — project-level principles, no-PHI rule, draft-status enforcement
2. **Know the hooks** — they're there to protect the project; if blocked, understand why and adjust your input
3. **Check the skill** — `/banner-health draft ...` and `/banner-health summarize ...` are available for testing workflows
4. **Review the audit log** — it's a historical record of all changes; use it to track project evolution

## Quick Reference

| Task | Command |
|------|---------|
| Draft a note | `/banner-health draft "..."`  |
| Summarize a chart | `/banner-health summarize "..."`  |
| View audit log | `tail docs/design/.audit-log`  |
| Test PHI hook | `bash .claude/hooks/check-phi.sh test.md "SSN 123-45-6789"` |
| Verify settings.json | `python3 -m json.tool .claude/settings.json` |
| Check hook permissions | `ls -la .claude/hooks/` |

---

See root `CLAUDE.md` for project-wide guidance. See `docs/design/high-level-design.md` for system architecture.
