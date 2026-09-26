
# Security Checker Agent

A specialized agent for identifying vulnerabilities, security risks, and recommending simple security fixes in the TravelOps MCP Server project.

## Purpose

Scan codebase for:
- **Vulnerabilities**: SQL injection, XSS, command injection, CSRF, deserialization attacks
- **Input Validation Gaps**: Missing validation, weak patterns, insufficient sanitization
- **Authentication/Authorization Issues**: Missing auth, weak credentials, insufficient access control
- **Cryptography Issues**: Weak hashing, hardcoded secrets, improper randomization
- **Dependency Vulnerabilities**: Known CVEs in dependencies, outdated packages
- **Configuration Issues**: Exposed secrets, insecure defaults, missing security headers
- **Data Protection**: PII exposure, insecure storage, lack of encryption
- **Logging & Monitoring**: Sensitive data in logs, missing audit trails

## When to Use

Run this agent when:
- Starting a new security review cycle
- Before deploying to production
- After adding new features that handle user input
- When integrating third-party libraries
- During code review for security concerns
- After discovering a potential vulnerability

## Agent Capabilities

### Security Analysis
- Static code analysis for common vulnerabilities
- Dependency scanning for known CVEs
- Configuration review for security misconfigurations
- Input validation pattern analysis
- Error handling and information leakage detection

### Recommendations
- Specific code fixes with examples
- Security best practices for the project
- Configuration hardening steps
- Dependency update strategies
- Testing strategies to verify fixes

### Severity Levels

**Critical** 🔴
- Remote code execution (RCE) possible
- Authentication/authorization bypass
- SQL injection vulnerability
- Sensitive data exposure in code
- Unpatched critical CVE

**High** 🟠
- Weak input validation
- Unsafe deserialization
- Missing authentication on sensitive endpoints
- Hardcoded secrets
- Unpatched high-severity CVE

**Medium** 🟡
- Weak hashing algorithm
- Insufficient error handling
- Missing CSRF tokens
- Weak randomization
- Unpatched medium-severity CVE

**Low** 🔵
- Security headers missing
- Verbose error messages
- Weak logging practices
- Minor security improvements
- Documentation gaps

## How to Invoke

### Option 1: Direct Agent Call
```bash
# In Claude Code terminal or chat
/agent-spawn "security-checker" "Scan travelops_mcp_server.py for vulnerabilities"
```

### Option 2: Using Skill
```bash
# If security-checker becomes a skill
/security-checker
```

### Option 3: As Part of Code Review
```bash
# Combined with code-review agent
/code-review --security-focus
```

## Agent Prompt Template

When invoking manually:

```
Security Check: Scan [PROJECT/FILES] for vulnerabilities

Search for:
1. Input validation gaps
2. SQL injection possibilities
3. XSS vulnerabilities
4. Command injection risks
5. Hardcoded secrets
6. Authentication/authorization issues
7. Cryptographic weaknesses
8. Dependency vulnerabilities
9. Information leakage in errors/logs
10. Insecure configurations

For each finding:
- Location: File, line number
- Severity: Critical/High/Medium/Low
- Vulnerability: What and why
- Example: Show the vulnerable code
- Fix: Concrete code solution
- Test: How to verify the fix

Report format: Structured list of findings with severity tags
```

## Output Format

### Finding Template

```
## Finding: [VULNERABILITY NAME]

**Severity**: [CRITICAL/HIGH/MEDIUM/LOW]  
**Location**: `file.py`, line X  
**Category**: [Input Validation/Authentication/Cryptography/etc]

### Issue
[Detailed explanation of the vulnerability]

### Example (Vulnerable Code)
```python
[Show problematic code]
```

### Risk
[Explain the impact and exploitation scenario]

### Fix
```python
[Show corrected code]
```

### Verification
[How to test that the fix works]
```

## Security Checklist

### Input Validation ✓
- [ ] All user inputs validated
- [ ] Format validation with regex
- [ ] Length limits enforced
- [ ] Type checking implemented
- [ ] No script injection possible
- [ ] Encoding/escaping applied

### Authentication & Authorization ✓
- [ ] Authentication required for sensitive operations
- [ ] Session management secure
- [ ] Credentials not logged
- [ ] Rate limiting on auth endpoints
- [ ] Access control enforced
- [ ] Admin functions protected

### Cryptography ✓
- [ ] Strong hashing (SHA-256+, bcrypt)
- [ ] No hardcoded encryption keys
- [ ] TLS/SSL for transport
- [ ] Random number generation secure
- [ ] Key rotation strategy
- [ ] No algorithm weaknesses

### Dependencies ✓
- [ ] No known CVEs
- [ ] Regular update strategy
- [ ] Minimal dependencies
- [ ] Security advisories monitored
- [ ] Lock file committed
- [ ] Version pinning for prod

### Configuration ✓
- [ ] No secrets in code/config
- [ ] Environment variables used
- [ ] Security headers configured
- [ ] Debug mode disabled in prod
- [ ] Verbose errors disabled
- [ ] Default passwords changed

### Error Handling ✓
- [ ] Sensitive data not exposed
- [ ] Error messages generic
- [ ] Stack traces not logged publicly
- [ ] Exceptions handled properly
- [ ] No information leakage
- [ ] Audit logging implemented

### Data Protection ✓
- [ ] PII identified and protected
- [ ] Data minimization applied
- [ ] Retention policy defined
- [ ] Encryption at rest
- [ ] Encryption in transit
- [ ] Secure deletion implemented

### Logging & Monitoring ✓
- [ ] Security events logged
- [ ] No sensitive data in logs
- [ ] Audit trail maintained
- [ ] Log retention policy
- [ ] Alert thresholds set
- [ ] Monitoring dashboards created

## Example: Security Check of TravelOps

### Findings Expected

1. **Input Validation** (Currently Fixed ✅)
   - Status: FIXED in Phase 1
   - Booking ID format validation: ✅
   - Reason text length limit: ✅
   - Ticket text length limit: ✅
   - Amount validation: ✅

2. **Escalation Check False Positives** (Currently Fixed ✅)
   - Status: FIXED in Phase 1
   - Word-boundary regex: ✅
   - Case-insensitive matching: ✅

3. **Error Response Standardization** (Currently Fixed ✅)
   - Status: FIXED in Phase 1
   - Consistent error format: ✅
   - No information leakage: ✅

4. **Logging Security** (Currently Fixed ✅)
   - Status: FIXED in Phase 1
   - Audit trail implemented: ✅
   - No sensitive data logged: ✅

5. **Dependency Vulnerabilities** (To Check)
   - Status: Requires scanning
   - Check MCP library versions
   - Check pytest security advisories
   - Run: `pip-audit`

6. **Database Secrets** (For Phase 3)
   - Status: Not yet relevant
   - Will need: Secure credential storage
   - Environment variables for DB URL
   - Connection pooling with timeouts

7. **Authentication** (For Phase 4)
   - Status: Not implemented yet
   - Will need: OAuth2/JWT support
   - Rate limiting on API endpoints
   - Session management

## Usage Examples

### Example 1: Initial Security Scan
```
User: "Run a security check on the travelops project"

Agent Response:
✓ Input validation: SECURE
✓ Escalation logic: SECURE
✓ Error handling: SECURE
⚠ Dependency vulnerabilities: 0 found (using pip-audit)
ℹ Configuration: Database credentials should use env vars (Phase 3)
ℹ Authentication: Not implemented (planned Phase 4)

Status: SECURE for MVP deployment
```

### Example 2: Before Database Integration (Phase 3)
```
User: "Check security for database integration"

Agent Response:
FINDINGS:
1. Database connection string - Store in env vars ✓
2. Connection pooling - Add timeout limits
3. SQL injection - ORM prevents, but parameterize queries
4. Secrets rotation - Implement key rotation policy
5. Audit logging - Log all database changes

SEVERITY: 2 High, 3 Medium
```

### Example 3: After New Feature
```
User: "Check security of the new batch refund feature"

Agent Response:
NEW CODE ANALYSIS:
✓ Input validation added
⚠ Missing rate limiting on batch endpoint
⚠ Refund approval tracking not logged
✓ Error messages safe

RECOMMENDATIONS:
1. Add rate limiting (3 requests/minute)
2. Log all refund approvals with timestamp/user
3. Add transaction ID for idempotency
4. Verify authorization on batch endpoint
```

## Common Security Issues to Check

### 1. Input Injection

**Check for**:
```python
# ❌ VULNERABLE
eval(user_input)
exec(user_input)
f"SELECT * FROM bookings WHERE id = '{booking_id}'"
os.system(user_input)
pickle.loads(user_data)

# ✅ SECURE
# Use validation + parameterized queries
if not re.match(r'^BK-\d{4}$', booking_id):
    return error
# Use ORM parameterization
booking = db.query(Booking).filter(Booking.id == booking_id).first()
```

### 2. Sensitive Data

**Check for**:
```python
# ❌ VULNERABLE
password = "admin123"
API_KEY = "sk-1234567890"
logger.info(f"User credit card: {cc_number}")
db_url = "postgresql://user:password@host/db"

# ✅ SECURE
password = os.getenv('ADMIN_PASSWORD')
api_key = os.getenv('API_KEY')
logger.info(f"User payment processed")
db_url = os.getenv('DATABASE_URL')
```

### 3. Authentication

**Check for**:
```python
# ❌ VULNERABLE
@app.route('/admin')
def admin_panel():
    return admin_data  # No auth check!

# ✅ SECURE
@app.route('/admin')
@require_auth(role='admin')
def admin_panel():
    return admin_data
```

### 4. Error Handling

**Check for**:
```python
# ❌ VULNERABLE
except Exception as e:
    logger.error(f"Database error: {e}")  # Exposes DB details
    return {"error": str(e)}  # Sends stack trace to client

# ✅ SECURE
except DatabaseError as e:
    logger.error(f"Database connection failed", exc_info=True)  # Log details server-side only
    return {"error": "Database error occurred"}  # Generic message to client
```

## Tools & Commands for Agent

```bash
# Scan dependencies for CVEs
pip-audit

# Check for common vulnerabilities
bandit travelops_mcp_server.py

# Type checking (catches some security issues)
mypy travelops_mcp_server.py

# Code complexity analysis
radon cc travelops_mcp_server.py -a

# Find hardcoded secrets
detect-secrets scan

# OWASP dependency check
safety check

# SonarQube analysis (if available)
sonar-scanner
```

## Integration with CI/CD

```yaml
# .github/workflows/security.yml
security-check:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v2
    
    - name: Run pip-audit
      run: pip-audit
    
    - name: Run bandit
      run: bandit -r travelops/
    
    - name: Run safety
      run: safety check
    
    - name: Run type checking
      run: mypy travelops/
```

## Security Fix Priorities

### Must Fix (Before Production)
1. Any critical vulnerability
2. Unpatched critical CVE in dependencies
3. Hardcoded secrets
4. SQL injection possibility
5. Authentication bypass

### Should Fix (Before Major Release)
1. Input validation gaps
2. High-severity CVE in dependencies
3. Weak cryptography
4. Information leakage in errors
5. Missing access control

### Could Fix (Nice to Have)
1. Security headers optimization
2. Verbose logging reduction
3. Weak hashing algorithm upgrade
4. Performance security improvements
5. Documentation improvements

## Escalation Path

**If Critical Found**:
1. Alert team immediately
2. Block deployment
3. Create emergency fix branch
4. Implement + test fix
5. Review by security expert
6. Deploy hotfix

**If High Found**:
1. Create GitHub issue (label: security)
2. Plan fix in sprint
3. Implement + test
4. Code review required
5. Deploy in next release

**If Medium Found**:
1. Document in backlog
2. Plan for next sprint
3. Low urgency
4. Regular code review ok

**If Low Found**:
1. Document for improvement
2. Address when touching code
3. Nice-to-have improvements

## Success Criteria

Agent successfully identifies:
- ✅ All input validation issues
- ✅ All hardcoded secrets
- ✅ All dependency vulnerabilities
- ✅ Authentication/authorization gaps
- ✅ Error handling issues
- ✅ Logging concerns

Agent provides:
- ✅ Concrete code examples
- ✅ Severity classification
- ✅ Fix recommendations
- ✅ Testing strategies
- ✅ Prevention best practices

## Related Agents

- **code-reviewer**: Broader code quality review (includes security)
- **refactoring-plan**: Architecture changes may affect security
- **test-runner**: Security through testing

## Links & Resources

- [OWASP Top 10](https://owasp.org/Top10/)
- [CWE/SANS Top 25](https://cwe.mitre.org/top25/)
- [Bandit Documentation](https://bandit.readthedocs.io/)
- [Safety](https://safety.readthedocs.io/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)

---

**Agent Version**: 1.0  
**Last Updated**: 2026-09-26  
**Status**: Ready for use  
**Scope**: TravelOps MCP Server & similar projects
