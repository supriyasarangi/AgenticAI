# Security Fixer Agent

An automated remediation agent that identifies and fixes security vulnerabilities in the TravelOps MCP Server project.

## Purpose

Fix security issues found by the security-checker agent:
- **Automatic Fixes**: Apply code changes for common vulnerabilities
- **Manual Guidance**: Provide step-by-step fixes for complex issues
- **Verification**: Test fixes and confirm they resolve the vulnerability
- **Documentation**: Update code with security improvements and comments

## When to Use

Run this agent:
- After security-checker identifies vulnerabilities
- Before production deployment
- When adding new features with security concerns
- During security hardening phases
- Before phase transitions (especially Phase 3 & 4)

## Agent Capabilities

### Automatic Fixes

**Input Validation**
- ✅ Add regex pattern validation
- ✅ Add length limit checks
- ✅ Add type validation
- ✅ Add value range checks

**Error Handling**
- ✅ Replace verbose error messages with generic ones
- ✅ Remove sensitive data from error responses
- ✅ Add proper exception handling
- ✅ Implement error logging without sensitive data

**Logging Security**
- ✅ Remove sensitive fields from logs
- ✅ Add sanitization for user input in logs
- ✅ Implement structured logging
- ✅ Add audit trail markers

**Configuration**
- ✅ Move hardcoded values to environment variables
- ✅ Add security headers
- ✅ Implement rate limiting placeholders
- ✅ Add timeout configurations

**Dependencies**
- ✅ Update vulnerable packages
- ✅ Pin to specific secure versions
- ✅ Add security advisory checks

**Code Pattern Improvements**
- ✅ Fix weak regex patterns (add word boundaries)
- ✅ Replace unsafe operations with secure alternatives
- ✅ Add input encoding/escaping
- ✅ Implement secure defaults

### Manual Fixes (Guidance Provided)

- 🔧 Database security setup (Phase 3)
- 🔧 Authentication implementation (Phase 4)
- 🔧 Cryptographic key management
- 🔧 Access control enforcement
- 🔧 Certificate management

### Verification

- ✅ Run existing tests after each fix
- ✅ Create new tests for fixed vulnerabilities
- ✅ Verify no regressions introduced
- ✅ Confirm fix resolves the issue

## How to Invoke

### Method 1: Fix Specific Issue
```bash
/agent-spawn "security-fixer" "Fix SQL injection in get_booking function"
```

### Method 2: Fix All Issues
```bash
/agent-spawn "security-fixer" "Fix all vulnerabilities in travelops_mcp_server.py"
```

### Method 3: Fix Category
```bash
/agent-spawn "security-fixer" "Fix all input validation issues"
```

### Method 4: After Security Check
```bash
/agent-spawn "security-fixer" "Apply fixes from security-checker findings"
```

## Fixable Issues

### Category 1: Input Validation Gaps ✅ FIXABLE

**Example Issue**:
```python
# ❌ VULNERABLE - No validation
def get_booking(booking_id: str) -> dict:
    booking = BOOKINGS.get(booking_id)
```

**Automatic Fix**:
```python
# ✅ FIXED - With validation
BOOKING_ID_PATTERN = r'^BK-\d{4}$'

def get_booking(booking_id: str) -> dict:
    # Validate input format
    if not booking_id or not re.match(BOOKING_ID_PATTERN, booking_id):
        return {"error": "INVALID_BOOKING_ID"}
    
    booking = BOOKINGS.get(booking_id)
    if not booking:
        return {"error": f"Booking not found: {booking_id}"}
    return {"booking": booking}
```

### Category 2: Escalation Logic False Positives ✅ FIXABLE

**Example Issue**:
```python
# ❌ VULNERABLE - Substring matching causes false positives
if "legal" in ticket_text.lower():
    escalate = True
```

**Automatic Fix**:
```python
# ✅ FIXED - Word boundary matching
import re
pattern = re.compile(r'\blegal\b', re.IGNORECASE)
if pattern.search(ticket_text):
    escalate = True
```

### Category 3: Error Message Information Leakage ✅ FIXABLE

**Example Issue**:
```python
# ❌ VULNERABLE - Exposes internal details
except DatabaseError as e:
    return {"error": str(e)}  # Sends DB details to client
```

**Automatic Fix**:
```python
# ✅ FIXED - Generic message to client
except DatabaseError as e:
    logger.error(f"Database error: {e}", exc_info=True)  # Log details server-side
    return {"error": "Database error occurred"}  # Generic message to client
```

### Category 4: Sensitive Data in Logging ✅ FIXABLE

**Example Issue**:
```python
# ❌ VULNERABLE - Logs sensitive data
logger.info(f"Refund request: {booking}, reason: {reason}")
```

**Automatic Fix**:
```python
# ✅ FIXED - No sensitive data in logs
logger.info(
    f"Refund calculated",
    extra={
        "booking_id": booking_id,
        "refund_rate": refund_rate,
        "requires_approval": requires_approval
    }
)
# Customer name NOT logged
```

### Category 5: Hardcoded Configuration ✅ FIXABLE

**Example Issue**:
```python
# ❌ VULNERABLE - Secrets in code
DATABASE_URL = "postgresql://user:password@host/db"
API_KEY = "sk-1234567890"
```

**Automatic Fix**:
```python
# ✅ FIXED - Environment variables
import os

DATABASE_URL = os.getenv('DATABASE_URL')
API_KEY = os.getenv('API_KEY')

if not DATABASE_URL or not API_KEY:
    raise ValueError("Missing required environment variables")
```

### Category 6: Weak Pattern Matching ✅ FIXABLE

**Example Issue**:
```python
# ❌ VULNERABLE - Simple string matching
risky_terms = ["medical", "legal"]
for term in risky_terms:
    if term in ticket_text.lower():
        reasons.append(term)
```

**Automatic Fix**:
```python
# ✅ FIXED - Pre-compiled word-boundary patterns
ESCALATION_PATTERNS = {
    "medical": re.compile(r'\bmedical\b', re.IGNORECASE),
    "legal": re.compile(r'\blegal\b', re.IGNORECASE),
}

reasons = []
for term, pattern in ESCALATION_PATTERNS.items():
    if pattern.search(ticket_text):
        reasons.append(term)
```

### Category 7: Missing Type Hints ✅ FIXABLE

**Example Issue**:
```python
# ⚠️ INCOMPLETE - No return type
def calculate_refund(booking, reason):
    return {"refund": 1000}
```

**Automatic Fix**:
```python
# ✅ FIXED - Full type hints
from typing import TypedDict

class RefundResult(TypedDict):
    refund_amount_inr: int
    approval_required: bool

def calculate_refund(booking: BookingData, reason: str) -> RefundResult:
    return {"refund_amount_inr": 1000, "approval_required": True}
```

### Category 8: Missing Validation on Return ✅ FIXABLE

**Example Issue**:
```python
# ⚠️ INCOMPLETE - No bounds checking
refund_amount = int(booking["amount_inr"] * 0.7)  # Could be negative if amount is negative
```

**Automatic Fix**:
```python
# ✅ FIXED - Validated calculations
def validate_amount(amount: int) -> bool:
    return amount >= 0 and amount <= 10000000  # Reasonable bounds

amount = booking["amount_inr"]
if not validate_amount(amount):
    raise ValueError(f"Invalid booking amount: {amount}")

refund_amount = int(amount * 0.7)
assert refund_amount >= 0, "Refund calculation resulted in negative amount"
```

## Auto-Fix Process

### Step 1: Identify Issue
```
Issue: Input validation gap in get_booking()
Severity: HIGH
Type: Input Validation
```

### Step 2: Determine Fix Type
```
Fix Type: AUTOMATIC
Confidence: 100%
Impact: Code change required
```

### Step 3: Apply Fix
```python
# Modify travelops_mcp_server.py
# Add validation function
# Add pattern validation
# Test with existing tests
```

### Step 4: Verify Fix
```
✅ Tests pass: 58/58
✅ New test for fix: PASS
✅ Regression check: PASS
✅ Coverage maintained: 93%
```

### Step 5: Report Results
```
FIXED: Input validation gap in get_booking()
├─ File: travelops_mcp_server.py
├─ Lines: 220-235
├─ Tests: 5 new tests added
└─ Status: ✅ VERIFIED
```

## Fix Strategy by Severity

### CRITICAL Issues (Must Fix)
- ✅ Automatic fix applied
- ✅ Tests created for fix
- ✅ Manual verification required
- ✅ Commit immediately
- ✅ Blocks other work

### HIGH Issues (Should Fix)
- ✅ Automatic fix applied if possible
- 🔧 Manual fix with guidance if needed
- ✅ Tests created/updated
- ✅ Commit in current sprint
- ⏸️ Can proceed with caution

### MEDIUM Issues (Plan to Fix)
- ✅ Automatic fix applied if simple
- 🔧 Manual fix with detailed steps if complex
- ✅ Tests added
- ⏱️ Commit in next sprint
- ✅ No blocking

### LOW Issues (Nice to Fix)
- ✅ Automatic fix applied if trivial
- 🔧 Recommendations provided
- 📝 Documented for later
- ⏱️ Fix when touching related code
- ✅ No urgency

## Output Format

### For Automatic Fixes

```markdown
## Fixed: [Issue Name]

**Severity**: HIGH  
**Location**: travelops_mcp_server.py, line X  
**Type**: Input Validation

### What Was Fixed
[Description of the vulnerability]

### Before (Vulnerable)
```python
[Original vulnerable code]
```

### After (Secure)
```python
[Fixed secure code]
```

### Verification
- ✅ Tests: 58/58 passing
- ✅ New tests: 3 added
- ✅ Coverage: 93% maintained
- ✅ Regression: None detected

### Commit Message
```
Fix input validation in get_booking()

- Add booking ID format validation (regex: BK-####)
- Add length limit enforcement
- Add type checking
- Add 3 new test cases
- Maintains 93% coverage
```
```

### For Manual Fixes

```markdown
## Requires Manual Fix: [Issue Name]

**Severity**: HIGH  
**Location**: Phase 3 database integration  
**Type**: Database Security

### Issue
[Explanation of vulnerability]

### Why Automatic Fix Not Possible
- Requires database setup (Phase 3)
- Depends on ORM selection
- Architectural decision needed

### Manual Fix Steps
1. Step 1: [Specific action]
2. Step 2: [Specific action]
3. Step 3: [Specific action]

### Example (After Implementation)
```python
[Example of correct implementation]
```

### Testing
[How to verify the fix works]

### Estimated Effort
- Time: 2-4 hours
- Complexity: Medium
- Phase: 3 (Database Integration)
```

## Automatic Fix Categories

### 1. Validation Fixes
- ✅ Add regex patterns
- ✅ Add length checks
- ✅ Add range validation
- ✅ Add type conversion safety

### 2. Error Handling Fixes
- ✅ Replace verbose errors
- ✅ Add generic messages
- ✅ Implement safe logging
- ✅ Remove stack traces

### 3. Logging Fixes
- ✅ Remove sensitive fields
- ✅ Add field sanitization
- ✅ Implement audit logging
- ✅ Add contextual logging

### 4. Pattern Fixes
- ✅ Add word boundaries to regex
- ✅ Add case handling
- ✅ Add performance optimization
- ✅ Pre-compile patterns

### 5. Type Safety Fixes
- ✅ Add type hints
- ✅ Add return type validation
- ✅ Add parameter validation
- ✅ Add TypedDict definitions

### 6. Configuration Fixes
- ✅ Move to environment vars
- ✅ Add validation
- ✅ Add defaults
- ✅ Add fallbacks

## Manual Fix Categories

### 1. Database Security (Phase 3)
- 🔧 Connection string handling
- 🔧 Query parameterization
- 🔧 Connection pooling
- 🔧 Transaction management

### 2. Authentication (Phase 4)
- 🔧 OAuth2 implementation
- 🔧 JWT token handling
- 🔧 Session management
- 🔧 Password hashing

### 3. Authorization (Phase 4)
- 🔧 Role-based access control
- 🔧 Permission checking
- 🔧 Resource ownership
- 🔧 Audit logging

### 4. Cryptography
- 🔧 Key management
- 🔧 Algorithm selection
- 🔧 Certificate handling
- 🔧 Encryption at rest/transit

## Success Criteria

### For Each Fix
- ✅ All existing tests pass (58/58)
- ✅ New tests added for the fix
- ✅ Coverage maintained (≥93%)
- ✅ No regressions detected
- ✅ Code compiles without warnings
- ✅ Type hints complete

### Overall Success
- ✅ All CRITICAL issues fixed
- ✅ 80%+ of HIGH issues fixed
- ✅ Test suite still passes
- ✅ Coverage maintained
- ✅ Code quality improved
- ✅ Documentation updated

## Integration with CI/CD

```yaml
security-fix-workflow:
  trigger: security-findings
  steps:
    1. Run security-checker
    2. Parse findings
    3. Apply automatic fixes
    4. Run tests
    5. Report results
    6. Commit if all pass
    7. Create PR if any manual fixes
```

## Known Limitations

### Cannot Automatically Fix

- ❌ Database-related issues (requires Phase 3)
- ❌ Authentication issues (requires Phase 4)
- ❌ Architecture changes
- ❌ External service integration
- ❌ Policy decisions

### Will Require Manual Work

- 🔧 Complex architectural changes
- 🔧 New feature security
- 🔧 Third-party library integration
- 🔧 Deployment configuration
- 🔧 Infrastructure security

## Usage Examples

### Example 1: Fix All Automatic Issues
```
User: /agent-spawn "security-fixer" "Fix all automatic security issues"

Agent Response:
SCANNING... Found 12 fixable issues

FIXING:
1. ✅ Input validation in get_booking() - FIXED
2. ✅ Error message leakage - FIXED
3. ✅ Hardcoded config - FIXED
4. ✅ Weak regex patterns - FIXED
5. ✅ Logging sensitive data - FIXED
...

RESULTS:
- Fixed: 12
- Manual: 3
- Tests: All 58 passing + 8 new tests
- Coverage: 95% (improved from 93%)

Status: READY TO COMMIT
```

### Example 2: Fix Specific Category
```
User: /agent-spawn "security-fixer" "Fix all input validation issues"

Agent Response:
INPUT VALIDATION FIXES:
1. get_booking() - Added booking ID validation
2. estimate_refund() - Added reason length check
3. check_escalation() - Added ticket length check

RESULTS:
- Fixed: 3
- Tests: 3 new validation tests
- Status: ✅ ALL PASS
```

### Example 3: Fix with Verification
```
User: /agent-spawn "security-fixer" "Fix escalation check false positives and verify"

Agent Response:
ISSUE: Escalation check uses substring matching (false positives)

FIX APPLIED:
- Changed to word-boundary regex: r'\blegal\b'
- Pre-compiled patterns for performance
- Added case-insensitive matching

VERIFICATION:
✅ Test: test_false_positive_prevention_legal - PASS
✅ Test: test_case_insensitive_matching - PASS
✅ Regression: No issues detected
✅ Coverage: Maintained at 93%

Status: FIX VERIFIED AND COMMITTED
```

## Related Agents

- **security-checker**: Identifies vulnerabilities
- **code-reviewer**: Reviews code for quality
- **test-runner**: Verifies fixes with tests

## Workflow Integration

```
security-checker (identifies issues)
         ↓
security-fixer (applies fixes)
         ↓
test-runner (verifies fixes)
         ↓
code-reviewer (reviews changes)
         ↓
git commit (ready to merge)
```

## Command Examples

```bash
# Fix all automatic issues
/agent-spawn "security-fixer" "Fix all auto-fixable security issues"

# Fix specific issue
/agent-spawn "security-fixer" "Fix input validation gap in get_booking"

# Fix category
/agent-spawn "security-fixer" "Fix all input validation issues"

# Fix and verify
/agent-spawn "security-fixer" "Fix escalation false positives and test"

# Fix with reporting
/agent-spawn "security-fixer" "Fix issues and provide detailed report"
```

---

**Agent Version**: 1.0  
**Last Updated**: 2026-09-26  
**Status**: Ready for use  
**Scope**: TravelOps MCP Server & similar projects  
**Paired With**: security-checker agent
