
# Code Review Agent

A comprehensive end-to-end code review agent that analyzes projects for quality, security, architecture, and refactoring opportunities.

## Purpose

Review a codebase or project end-to-end and identify issues across multiple dimensions to support refactoring and improvement efforts.

## Scope

This agent analyzes:

1. **Code Quality** - style, structure, readability, maintainability
2. **Architecture** - design patterns, separation of concerns, extensibility
3. **Error Handling** - edge cases, error messages, validation
4. **Security** - input validation, sensitive data handling, injection risks
5. **Testing** - test coverage, missing tests, mockability
6. **Documentation** - docstrings, comments, usage clarity
7. **Performance** - inefficiencies, scalability issues
8. **Configuration** - environment setup, deployment readiness
9. **Framework-Specific** - MCP patterns, FastAPI patterns, Django patterns (context-dependent)

## Severity Levels

Issues are categorized as:

- **Critical**: Security vulnerabilities, data loss risks, production outages
- **High**: Major architectural flaws, missing tests, incomplete error handling
- **Medium**: Performance issues, configuration gaps, policy mismatches
- **Low**: Style improvements, documentation gaps, minor refactoring opportunities

## Output Format

Findings organized by:

1. **Issue category** (Security, Architecture, Testing, etc.)
2. **Severity level** (Critical → Low)
3. **Location** (File, line numbers)
4. **Description** (What, why, impact)
5. **Recommendation** (How to fix)

Include a summary table of all issues by severity and a prioritized refactoring roadmap.

## How to Invoke

```bash
/agent-spawn "code-reviewer" "Review the project at [PATH]"
```

Or via Agent tool with this prompt:

```
Review the project at [PATH] end-to-end. Analyze code quality, architecture, security, testing, documentation, performance, configuration, and framework-specific patterns. Categorize findings by severity (critical/high/medium/low). Provide specific recommendations for each issue.
```

## Example Usage

**Input:** 
```
Review /home/labuser/Downloads/Day_3 end-to-end for code quality and security issues.
```

**Output:**
- Critical issues (security, data loss)
- High-priority issues (architecture, testing gaps)
- Medium-priority issues (performance, config)
- Low-priority issues (style, docs)
- Refactoring roadmap with priorities

## Notes

- This is a read-only analysis agent — it does not modify code
- For applying fixes, refer to refactoring tasks or code generation agents
- Findings can be tracked as GitHub issues or task items for prioritization
- Re-run after major refactoring to verify improvements
