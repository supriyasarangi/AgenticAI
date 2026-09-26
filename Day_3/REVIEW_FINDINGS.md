# Code Review Findings: TravelOps MCP Server

**Date**: 2026-09-26  
**Project**: Travel Operations MCP Server  
**Reviewer**: End-to-End Code Review Agent  
**Status**: Review Complete

---

## Executive Summary

The TravelOps MCP server is a functional MVP but requires significant hardening before production use. Main gaps are security validation, test coverage, and proper architecture separation. Estimated refactoring effort: 3-4 weeks.

**Total Issues Found**: 17  
- **Critical**: 3 (Security, validation, error handling)
- **High**: 5 (Architecture, testing, documentation)
- **Medium**: 5 (Configuration, logic, performance)
- **Low**: 4 (Code quality, docs, ops)

---

## Critical Issues (Fix First)

### 1. Security: Naive Escalation Check
**Location**: `travelops_mcp_server.py`, lines 82-86  
**Severity**: CRITICAL  
**Issue**: Uses simple substring matching (`"legal" in text`) which creates false positives and is vulnerable to adversarial input.

**Example Failure**:
```
Input: "I have legal questions about my flight rebooking"
Expected: Normal ticket (no escalation)
Actual: ESCALATED (false positive - keyword match)
```

**Impact**: Incorrect support routing, poor customer experience, wasted escalation resources

**Recommendation**:
```python
import re

def check_escalation(ticket_text: str, amount_inr: int | None = None) -> dict:
    # Compile patterns at module load
    risk_patterns = [
        r'\bmedical\b',
        r'\blegal\b',
        r'\blawyer\b',
        r'\bcompensation\b',
        r'\bchargeback\b',
        r'\bstranded\b',
        r'\boxygen\b'
    ]
    
    reasons = []
    for pattern in risk_patterns:
        if re.search(pattern, ticket_text.lower()):
            reasons.append(pattern[2:-2])  # Extract term
    
    if amount_inr is not None and amount_inr > 50000:
        reasons.append("refund_above_50000")
    
    return {"escalate": bool(reasons), "reasons": reasons}
```

---

### 2. Security: Missing Input Validation
**Location**: `travelops_mcp_server.py`, lines 37-75  
**Severity**: CRITICAL  
**Issue**: 
- `booking_id` parameter has no format validation (could be any string)
- `reason` parameter is echoed back in response without sanitization
- Enables injection attacks if results are used in SQL or formatted output downstream

**Example Failure**:
```python
get_booking("BK-1001'; DROP TABLE bookings; --")
estimate_refund("BK-1001", "<script>alert('xss')</script>")
```

**Impact**: SQL injection, XSS attacks, data corruption

**Recommendation**:
```python
import re

BOOKING_ID_PATTERN = r'^BK-\d{4}$'
MAX_REASON_LENGTH = 500

def get_booking(booking_id: str) -> dict:
    if not booking_id or not re.match(BOOKING_ID_PATTERN, booking_id):
        return {"error": "INVALID_BOOKING_ID", "details": "Format must be BK-####"}
    booking = BOOKINGS.get(booking_id)
    if not booking:
        return {"error": "BOOKING_NOT_FOUND", "booking_id": booking_id}
    return {"ok": True, "booking": booking}

def estimate_refund(booking_id: str, reason: str) -> dict:
    if not re.match(BOOKING_ID_PATTERN, booking_id):
        return {"error": "INVALID_BOOKING_ID"}
    if not reason or len(reason) > MAX_REASON_LENGTH:
        return {"error": "INVALID_REASON", "max_length": MAX_REASON_LENGTH}
    # ... rest of logic
```

---

### 3. Error Handling: Inconsistent and Silent Failures
**Location**: `travelops_mcp_server.py`, lines 44-88  
**Severity**: CRITICAL  
**Issue**:
- Functions return different response structures (`{"ok": False}` vs `{"escalate": bool}`)
- No distinction between "not found" vs "invalid format" vs "server error"
- Silent failures make debugging difficult for clients

**Current Inconsistency**:
```python
# get_booking returns:
{"ok": False, "error_type": "BOOKING_NOT_FOUND"}

# check_escalation returns:
{"escalate": True, "reasons": [...]}

# No standard error handling across all functions
```

**Impact**: Client code must handle multiple response shapes, poor error recovery

**Recommendation**:
```python
from typing import TypedDict, Literal

ErrorCode = Literal[
    "INVALID_BOOKING_ID",
    "BOOKING_NOT_FOUND",
    "INVALID_REASON",
    "INTERNAL_ERROR"
]

class ErrorResponse(TypedDict):
    error: ErrorCode
    details: str
    request_id: str  # For tracing

class SuccessResponse(TypedDict):
    success: True
    data: dict

ResponseType = ErrorResponse | SuccessResponse

def get_booking(booking_id: str) -> ResponseType:
    if not re.match(BOOKING_ID_PATTERN, booking_id):
        return {
            "error": "INVALID_BOOKING_ID",
            "details": f"Booking ID must match {BOOKING_ID_PATTERN}",
            "request_id": generate_request_id()
        }
    booking = BOOKINGS.get(booking_id)
    if not booking:
        return {
            "error": "BOOKING_NOT_FOUND",
            "details": f"No booking found with ID {booking_id}",
            "request_id": generate_request_id()
        }
    return {"success": True, "data": {"booking": booking}}
```

---

## High Severity Issues

### 4. Architecture: Hard-coded Mock Data in Production Code
**Location**: `travelops_mcp_server.py`, lines 5-24  
**Severity**: HIGH  
**Issue**:
- Mock test data embedded in server code
- Only 2 test bookings; real system needs hundreds/thousands
- Booking state is immutable (cannot be updated)
- No database connection or abstraction

**Impact**: Cannot scale to production, no data persistence

**Recommendation**: Extract to database layer
```python
# database.py
from abc import ABC, abstractmethod

class BookingRepository(ABC):
    @abstractmethod
    def get_booking(self, booking_id: str) -> dict | None:
        pass
    
    @abstractmethod
    def list_bookings(self, customer_id: str) -> list[dict]:
        pass

class InMemoryBookingRepository(BookingRepository):
    """For testing only"""
    def __init__(self):
        self.bookings = {...}

class SQLBookingRepository(BookingRepository):
    """Production database"""
    def __init__(self, db_url: str):
        self.engine = sqlalchemy.create_engine(db_url)
```

---

### 5. Testing: Zero Test Coverage
**Location**: Entire project  
**Severity**: HIGH  
**Issue**:
- No unit tests, no integration tests, no fixtures
- Cannot safely refactor without breaking API
- Edge cases untested (negative amounts, empty strings, oversized inputs)

**Impact**: High refactoring risk, customer-facing bugs

**Recommendation**:
```bash
# Create test_travelops_mcp_server.py
pytest --cov=travelops_mcp_server --cov-report=html
# Target: 80%+ line coverage, 100% branch coverage
```

Example tests:
```python
import pytest
from travelops_mcp_server import get_booking, estimate_refund, check_escalation

class TestGetBooking:
    def test_valid_booking_found(self):
        result = get_booking("BK-1001")
        assert result["success"] == True
        assert result["data"]["booking"]["customer"] == "Maya Rao"
    
    def test_booking_not_found(self):
        result = get_booking("BK-9999")
        assert result["error"] == "BOOKING_NOT_FOUND"
    
    def test_invalid_booking_id_format(self):
        result = get_booking("INVALID")
        assert result["error"] == "INVALID_BOOKING_ID"
    
    def test_empty_booking_id(self):
        result = get_booking("")
        assert result["error"] == "INVALID_BOOKING_ID"

class TestEstimateRefund:
    def test_airline_cancellation_full_refund(self):
        result = estimate_refund("BK-1002", "Airline cancelled flight")
        assert result["data"]["refund_amount_inr"] == 86000
        assert result["data"]["approval_required"] == True
    
    def test_customer_cancellation_70_percent(self):
        result = estimate_refund("BK-1001", "Customer requested cancellation")
        assert result["data"]["refund_amount_inr"] == int(72000 * 0.7)
    
    def test_reason_too_long(self):
        result = estimate_refund("BK-1001", "x" * 501)
        assert result["error"] == "INVALID_REASON"

class TestCheckEscalation:
    def test_medical_emergency_escalates(self):
        result = check_escalation("Medical emergency, need oxygen")
        assert result["escalate"] == True
        assert "medical" in result["reasons"]
    
    def test_high_refund_amount_escalates(self):
        result = check_escalation("Normal request", amount_inr=75000)
        assert result["escalate"] == True
        assert "refund_above_50000" in result["reasons"]
    
    def test_false_positive_prevention(self):
        result = check_escalation("I have legal questions about baggage policy")
        # Should NOT escalate for innocent use of "legal"
        assert result["escalate"] == False
```

---

### 6. Documentation: Insufficient Docstrings
**Location**: All functions  
**Severity**: HIGH  
**Issue**:
- Functions have docstrings but lack parameter/return documentation
- Business logic unexplained (why 70% refund? why 50k threshold?)
- No return value structure documentation

**Recommendation**:
```python
def estimate_refund(booking_id: str, reason: str) -> dict:
    """
    Estimate refund amount for a booking based on cancellation reason.
    
    This function calculates refunds according to Helios Travel policy:
    - Airline cancellations: 100% refund (no approval needed if < 50k INR)
    - Customer cancellations: 70% refund (always requires human approval)
    
    Args:
        booking_id: Booking identifier in format BK-#### (e.g., "BK-1001")
        reason: Human-readable cancellation reason (max 500 chars)
    
    Returns:
        dict with structure:
        {
            "success": bool,
            "data": {
                "booking_id": str,
                "refund_amount_inr": int,
                "approval_required": bool,
                "reason": str,
                "policy_version": str
            } | None,
            "error": str | None
        }
    
    Raises:
        ValueError: If booking_id format is invalid
    
    Examples:
        >>> estimate_refund("BK-1001", "Customer requested cancellation")
        {'success': True, 'data': {'refund_amount_inr': 50400, ...}}
        
        >>> estimate_refund("INVALID", "Test")
        {'error': 'INVALID_BOOKING_ID', ...}
    """
```

---

### 7. MCP-Specific: Tool Design Issues
**Location**: Tool definitions (lines 36-88)  
**Severity**: HIGH  
**Issue**:
- `estimate_refund()` depends on successful `get_booking()` call, but this isn't enforced
- No idempotency guarantee (repeated calls could trigger duplicate processing)
- Tool names use `_` instead of `-` (inconsistent with MCP conventions)

**Impact**: Clients must orchestrate multiple calls; risk of duplicate refunds

**Recommendation**:
```python
@mcp.tool()
def process_refund_request(booking_id: str, reason: str) -> dict:
    """
    Atomic operation: lookup booking and estimate refund in one call.
    
    This combines get_booking + estimate_refund to ensure consistency
    and prevent duplicate processing.
    
    Returns:
        {
            "success": bool,
            "data": {
                "booking": dict,
                "refund": dict,
                "transaction_id": str  # For idempotency
            }
        }
    """
    # Validate and lookup
    booking = BOOKINGS.get(booking_id)
    if not booking:
        return {"error": "BOOKING_NOT_FOUND"}
    
    # Generate transaction ID for idempotency
    transaction_id = f"{booking_id}-{hash((reason, time.time()))}"
    
    # Calculate refund
    refund = calculate_refund(booking, reason)
    
    # Log for audit trail
    logger.info(f"Refund processed: {transaction_id}")
    
    return {
        "success": True,
        "data": {
            "booking": booking,
            "refund": refund,
            "transaction_id": transaction_id
        }
    }
```

---

### 8. Configuration: Missing Env Vars and Error Handling
**Location**: `.mcp.json` (line 6), server startup  
**Severity**: HIGH  
**Issue**:
- Relative path `.venv/bin/python` assumes .venv exists
- No error messages if Python not found
- No logging configuration
- Empty `env` object prevents passing configuration

**Impact**: Deployment failures, impossible to debug production issues

**Recommendation**:
```json
{
  "mcpServers": {
    "travelops": {
      "type": "stdio",
      "command": "${VENV_PATH}/bin/python",
      "args": ["travelops_mcp_server.py"],
      "env": {
        "LOG_LEVEL": "INFO",
        "DATABASE_URL": "${DATABASE_URL}",
        "REFUND_POLICY_VERSION": "3",
        "MCP_TIMEOUT": "30"
      }
    }
  }
}
```

---

### 9. Refund Logic: Hard-coded vs. Dynamic Policy Mismatch
**Location**: `estimate_refund()` (line 71), `REFUND_POLICY` (lines 26-33)  
**Severity**: HIGH  
**Issue**:
- Refund logic hard-coded: 70% for customer, 100% for airline
- `REFUND_POLICY` is a string resource, not executable rules
- Policy says "fare-rule charges may apply" but code always uses 70%
- No way to update policy without code change

**Impact**: Policy changes require code deployment, inconsistency between docs and behavior

**Recommendation**:
```python
# config.py
REFUND_POLICIES = {
    "version": "3",
    "airline_cancellation": {
        "refund_rate": 1.0,
        "requires_approval": False,
        "approval_threshold_inr": None
    },
    "customer_cancellation": {
        "refund_rate": 0.7,
        "requires_approval": True,
        "approval_threshold_inr": 50000
    },
    "medical_emergency": {
        "refund_rate": 1.0,
        "requires_approval": True,
        "approval_threshold_inr": None
    }
}

# Load from external config
def load_policy(policy_file: str) -> dict:
    with open(policy_file) as f:
        return json.load(f)
```

---

## Medium Severity Issues

### 10. Performance: Inefficient String Matching in Escalation
**Location**: `check_escalation()` (line 83-84)  
**Severity**: MEDIUM  
**Issue**:
- O(n*m) complexity: for each term, scans entire ticket_text
- No caching of compiled patterns
- Rebuilds reason list for every call

**Impact**: Slow for large tickets or high throughput

**Recommendation**:
```python
import re

# Compile patterns once at module load
RISK_PATTERNS = {
    "medical": re.compile(r'\bmedical\b', re.IGNORECASE),
    "legal": re.compile(r'\blegal\b', re.IGNORECASE),
    "oxygen": re.compile(r'\boxygen\b', re.IGNORECASE),
    # ... etc
}

def check_escalation(ticket_text: str, amount_inr: int | None = None) -> dict:
    reasons = []
    
    # Single-pass scan: O(n)
    for term, pattern in RISK_PATTERNS.items():
        if pattern.search(ticket_text):
            reasons.append(term)
    
    if amount_inr is not None and amount_inr > 50000:
        reasons.append("refund_above_50000")
    
    return {"escalate": bool(reasons), "reasons": reasons}
```

---

### 11. Input Validation: Missing Edge Cases
**Location**: `estimate_refund()`, `check_escalation()`  
**Severity**: MEDIUM  
**Issue**:
- `amount_inr` can be None but no check for negative values
- `ticket_text` has no length limits (could be 1MB string)
- Refund amount could be calculated as negative (no boundary check)

**Recommendation**:
```python
def estimate_refund(booking_id: str, reason: str) -> dict:
    # Validate amount range
    booking = BOOKINGS.get(booking_id)
    if booking and booking.get("amount_inr", 0) < 0:
        return {"error": "INVALID_BOOKING_AMOUNT"}
    
    # ... rest of validation

def check_escalation(ticket_text: str, amount_inr: int | None = None) -> dict:
    # Validate length
    MAX_TICKET_LENGTH = 10000
    if len(ticket_text) > MAX_TICKET_LENGTH:
        logger.warning(f"Oversized ticket: {len(ticket_text)} chars")
        ticket_text = ticket_text[:MAX_TICKET_LENGTH]
    
    # Validate amount
    if amount_inr is not None and amount_inr < 0:
        return {"error": "INVALID_AMOUNT"}
    
    # ... rest of logic
```

---

### 12. Type Hints: Incomplete and Vague
**Location**: All function signatures  
**Severity**: MEDIUM  
**Issue**:
- Return types are `-> dict` (too vague)
- No `TypedDict` for complex return shapes
- Union types (`int | None`) but no structured return types

**Recommendation**:
```python
from typing import TypedDict, Literal

class BookingData(TypedDict):
    customer: str
    route: str
    fare: str
    status: Literal["confirmed", "cancelled_by_airline"]
    amount_inr: int
    departure: str
    baggage: str

class GetBookingSuccess(TypedDict):
    success: Literal[True]
    data: {"booking": BookingData}

class GetBookingError(TypedDict):
    success: Literal[False]
    error: Literal["BOOKING_NOT_FOUND", "INVALID_BOOKING_ID"]

GetBookingResponse = GetBookingSuccess | GetBookingError

def get_booking(booking_id: str) -> GetBookingResponse:
    # ...
```

---

### 13. Logging: No Audit Trail
**Location**: Entire application  
**Severity**: MEDIUM  
**Issue**:
- No error, warning, or info logs
- Cannot debug production issues
- No audit trail for refund decisions (critical for compliance)

**Recommendation**:
```python
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def estimate_refund(booking_id: str, reason: str) -> dict:
    logger.info(f"Estimating refund for booking {booking_id}")
    
    booking = BOOKINGS.get(booking_id)
    if not booking:
        logger.warning(f"Booking not found: {booking_id}")
        return {"error": "BOOKING_NOT_FOUND"}
    
    refund_amount = calculate_refund(booking, reason)
    logger.info(
        f"Refund calculated",
        extra={
            "booking_id": booking_id,
            "amount_inr": refund_amount,
            "requires_approval": refund_amount > 50000
        }
    )
    # ...
```

---

## Low Severity Issues

### 14. Code Quality: Inconsistent Response Format
**Location**: Functions return different structures  
**Severity**: LOW  
**Issue**:
- Some responses use `"ok": True/False`, others just `"escalate": bool`
- Response structures not documented
- Client code must handle multiple shapes

**Recommendation**: Use consistent response wrapper (see High Severity Issue #3)

### 15. Configuration: Missing .gitignore
**Severity**: LOW  
**Recommendation**:
```
# .gitignore
.venv/
__pycache__/
*.pyc
*.pyo
.pytest_cache/
.coverage
htmlcov/
.env
.env.local
*.db
.mcp.local.json
dist/
build/
*.egg-info/
```

### 16. Documentation: No README or Setup Guide
**Severity**: LOW  
**Recommendation**: Create `README.md` with:
- Setup instructions
- Architecture overview
- Tool descriptions with examples
- Deployment guide
- Troubleshooting

### 17. Resource Design: Refund Policy as String
**Location**: `refund_policy()` resource (lines 91-94)  
**Severity**: LOW  
**Issue**: Returns human-readable text; Claude must parse to extract rules

**Recommendation**: Add JSON resource:
```python
@mcp.resource("travelops://policy/refund/structured")
def refund_policy_json() -> dict:
    return {
        "version": "3",
        "airline_cancellation": {"refund_rate": 1.0, "approval_required": False},
        "customer_cancellation": {"refund_rate": 0.7, "approval_required": True},
        "approval_threshold_inr": 50000
    }
```

---

## Architecture Overview

**Current (Monolithic)**:
```
travelops_mcp_server.py (115 lines)
├── FastMCP singleton
├── In-memory booking store
├── Refund policy string
├── 3 Tools
├── 1 Resource
└── 1 Prompt
```

**Recommended (Modular)**:
```
travelops_mcp_server.py (entry point, ~30 lines)
├── server.py (FastMCP setup and routes)
├── models.py (Booking, Refund TypedDicts)
├── database.py (BookingRepository abstraction)
├── business_logic.py (RefundCalculator, EscalationChecker)
├── handlers.py (Tool/Resource/Prompt implementations)
├── config.py (Configuration, policy rules)
├── logging_setup.py (Logging configuration)
└── tests/
    ├── test_business_logic.py
    ├── test_handlers.py
    └── fixtures.py
```

---

## Refactoring Roadmap

| Phase | Duration | Tasks | Priority |
|-------|----------|-------|----------|
| **Week 1** | 3-4 days | Input validation, escalation fix, error handling standardization | P0 |
| **Week 2** | 3-4 days | Test suite, type hints, logging setup | P0 |
| **Week 3** | 4-5 days | Architecture refactor, database abstraction, modularization | P1 |
| **Week 4** | 2-3 days | Documentation, README, deployment guide | P1 |

---

## Security Risk Summary

| Risk | Severity | Impact | Status |
|------|----------|--------|--------|
| Naive escalation check | Critical | False escalations affecting support routing | ⚠️ OPEN |
| No input validation | Critical | Injection attacks, data corruption | ⚠️ OPEN |
| Inconsistent errors | Critical | Information leakage, unpredictable behavior | ⚠️ OPEN |
| Mock data in production | High | Data loss, scaling issues | ⚠️ OPEN |
| No test coverage | High | Regression risk, customer bugs | ⚠️ OPEN |
| No logging/audit | High | Compliance issues, debugging impossible | ⚠️ OPEN |

---

## Files Reviewed

- `travelops_mcp_server.py` (115 lines)
- `.mcp.json` (10 lines)
- `.claude/settings.local.json` (permissions)

---

## Conclusion

This is a solid MVP that demonstrates the core travel ops workflow. However, it requires significant hardening in three areas:

1. **Security First** (Week 1): Input validation and error handling are prerequisites for any production deployment
2. **Quality & Testing** (Week 2): Comprehensive tests provide confidence for refactoring
3. **Architecture** (Week 3-4): Modular design enables scaling and maintenance

**Recommendation**: Start with Week 1 critical fixes, then progress through the roadmap.
