# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project: TravelOps MCP Server

An MCP server for Helios Travel support automation. Handles booking lookups, refund estimation, and escalation detection. Currently Phase 1 (MVP with security hardening).

## Quick Commands

```bash
# Setup
source .venv/bin/activate
pip install -r requirements.txt

# Run server
python travelops_mcp_server.py

# Run all tests
pytest test_travelops_mcp_server.py -v

# Run with coverage
pytest test_travelops_mcp_server.py -v --cov=travelops_mcp_server --cov-report=html

# Run specific test class
pytest test_travelops_mcp_server.py::TestGetBooking -v

# Run single test
pytest test_travelops_mcp_server.py::TestCheckEscalation::test_medical_emergency_escalates -v

# Check for diagnostics
python -m pylance check travelops_mcp_server.py
```

## Architecture Overview

**Single-file design** (intentional MVP pattern):
```
travelops_mcp_server.py
├── Type Definitions (BookingData, ErrorResponse, etc. using TypedDict)
├── Configuration Section (BOOKING_ID_PATTERN, MAX_REASON_LENGTH, etc.)
├── Validation Functions (5 functions: booking_id, reason, ticket_text, amount, + calculate_refund)
├── MCP Tools (3 decorated functions: get_booking, estimate_refund, check_escalation)
├── MCP Resources (2: refund policy as text + structured JSON)
├── MCP Prompts (1: triage_travel_ticket template)
└── Server Startup
```

**Key Design Decisions:**
- **MCP 2.x Compatibility**: Code handles both MCP 2.x (MCPServer) and 1.x (FastMCP) via try/except import
- **Validation First**: All inputs validated before processing (regex format, length limits, type checks)
- **Compiled Patterns**: ESCALATION_PATTERNS compiled at startup (O(n) single-pass scan, not O(n*m))
- **Structured Policy**: Refund policy in TypedDict-friendly dict format (not string parsing)
- **Consistent Errors**: All tools return `{"error": "message"}` on failure, success data varies by tool
- **Audit Logging**: All significant operations logged with context (booking_id, amounts, reasons, escalation triggers)

## Code Organization

### Validation Layer (Lines ~140-200)
Five validation functions handle input constraints. Always called before tool logic:
- `validate_booking_id()` → regex `^BK-\d{4}$`
- `validate_reason()` → max 500 chars
- `validate_ticket_text()` → max 10,000 chars
- `validate_amount()` → no negatives
- `calculate_refund()` → derives approval logic from policy struct

### Business Logic (Lines ~200-240)
`calculate_refund()` determines approval need based on:
1. Booking status (airline vs customer cancellation)
2. Refund rate lookup in REFUND_POLICY_STRUCTURED
3. Threshold comparison (e.g., > 50k INR triggers approval for customer cancellations)

### MCP Tools (Lines ~240-340)
Three decorated tools. Each:
1. Validates all inputs (calls validate_* functions)
2. Logs entry/errors/results
3. Returns consistent error response on validation failure
4. Executes business logic
5. Returns typed response with all fields present

**Pattern**: All tools follow: validate → log entry → lookup/calculate → log result → return

### MCP Resources & Prompts (Lines ~340-380)
- `refund_policy()` → human-readable text (used by Claude for context)
- `refund_policy_structured()` → JSON dict for programmatic access
- `triage_travel_ticket()` → multi-step prompt template for ticket triage

## Testing Strategy

**58 tests organized in 8 test classes:**
1. **Validation Tests** (22 tests) - Format, length, type boundaries
2. **Business Logic** (4 tests) - Refund calculations with different statuses
3. **Tool Tests** (28 tests) - Happy/sad paths for each of 3 tools
4. **Edge Cases** (5 tests) - Integration workflows, state immutability

**Coverage Target**: 80%+ line, 100% branch for tools

**Test Patterns:**
- Each tool has success + failure cases (not found, invalid format, etc.)
- Validation tests check boundaries (empty, max-length, over-limit, negative)
- Edge cases verify state doesn't change across calls
- Special chars in reason don't cause crashes

**To debug a failing test**:
```bash
pytest test_travelops_mcp_server.py::TestCheckEscalation::test_false_positive_prevention_legal -vv --tb=short
```

## Important Patterns & Conventions

### Input Validation
- **All** external inputs validated before use (not just at tool boundary)
- Regex patterns use word boundaries (`\b...\b`) to prevent false matches
- Length limits enforced (reason max 500, ticket max 10,000)
- No SQL/injection concerns yet (in-memory test data), but structure supports future DB

### Error Handling
**Standardized error response:**
```python
{"error": "INVALID_BOOKING_ID", "details": "Format must be BK-####"}
```
Not: `{"ok": False, "error_type": "..."}` (old inconsistent style)

**Logging pattern:**
```python
logger.warning(f"Invalid booking ID format: {booking_id}")
return {"error": "INVALID_BOOKING_ID"}
```

### Escalation Check (Most Complex Tool)
Uses **word-boundary regex** (not substring match) to prevent false positives:
- ✅ Correctly escalates "I have a medical emergency"
- ❌ Should NOT escalate "generally pleasant" (contains "legal" in "generally")
- Implementation: Loop through compiled ESCALATION_PATTERNS, check multiple risk factors

### Refund Policy Logic
Policy encoded as:
```python
REFUND_POLICY_STRUCTURED = {
    "airline_cancellation": {"refund_rate": 1.0, "requires_approval": False, ...},
    "customer_cancellation": {"refund_rate": 0.7, "requires_approval": True, ...}
}
```
**Not** hard-coded in tool functions. Future phases can load from database or config file without code changes.

## Known Limitations (Phase 1)

- ✅ Input validation complete
- ✅ Test coverage at 80%+
- ❌ In-memory only (2 test bookings)
- ❌ No authentication
- ❌ No database backend
- ❌ No batch processing
- ❌ No persistence for refund requests (can't detect duplicates)

## Next Phases (Week 3-4)

### Phase 2: Architecture Refactor (Week 3)
- Extract to modular structure (separate business_logic.py, database.py, handlers.py)
- Abstract BookingRepository (enables in-memory testing + prod DB)
- Add transaction IDs for idempotency tracking

### Phase 3: Database Integration (Week 4)
- PostgreSQL backend (or SQLite for dev)
- Connection pooling
- Booking persistence
- Audit logging to durable storage

### Phase 4: Enterprise Features (Future)
- OAuth2/JWT authentication
- Role-based access control
- Batch refund processing
- Webhook notifications
- Rate limiting

## Gotchas & Common Issues

### Escalation Check False Positives
The old code used `"legal" in ticket_text` which matches inside "generally" or "illegal". Current code uses word boundaries (`\blegal\b`) which is correct.
- If adding new escalation terms, always use `\bterm\b` pattern
- Test with phrases like "I have legal questions" vs "It's illegal" vs "generally fine"

### Refund Amount Must Be Integer
Tests verify `isinstance(refund_amount, int)`. Using `.7 * amount` can produce floats.
- Use `int(amount * 0.7)` not `amount * 0.7`
- Flooring is intentional (no partial rupees)

### MCP Compatibility
Code supports both MCP 2.x and 1.x via try/except import. If upgrading MCP:
1. Test both versions if possible
2. Remove fallback once MCP 2.x is required project-wide
3. Update requirements.txt version constraints

### Logging Is Synchronous
Currently logs to console. Phase 2-3 should add file logging for production audit trail.
- Avoid logging sensitive data (payment card details, etc.)
- Log: booking_id, amounts, escalation reasons, validation errors
- Don't log: customer names (can extract from booking_id if needed)

## When Modifying Core Functions

**get_booking()**: Currently lookup-only. If adding state changes (mark viewed, etc.):
- Must add transaction tracking (booking_id + timestamp)
- Update tests to verify state didn't change unexpectedly
- Consider idempotency

**estimate_refund()**: Calculation-only. If moving money:
- Add approval workflow (separate step, don't compute + execute in same function)
- Add transaction IDs to track duplicate requests
- Implement idempotency: same booking_id + reason = same result

**check_escalation()**: If adding new escalation terms:
- Always test word-boundary patterns to prevent false positives
- Add test cases for phrases using that word (e.g., test_TERM_escalates + test_term_false_positive)
- Document why the term is a risk (medical, legal, financial, etc.)

## Project Files

- `travelops_mcp_server.py` — Main server (Phase 1 complete: ~400 lines, single file by design)
- `test_travelops_mcp_server.py` — 58 comprehensive tests (~700 lines)
- `.mcp.json` — MCP server registration (stdio-based)
- `.gitignore` — Excludes .venv, __pycache__, .pytest_cache, etc.
- `requirements.txt` — MCP, pytest, python-dotenv
- `README.md` — API docs, tool descriptions, examples
- `REVIEW_FINDINGS.md` — Complete code review (17 issues documented)

## Review and Refactoring History

**Recent changes** (Phase 1 completed 2026-09-26):
- ✅ Fixed naive escalation check (substring → word-boundary regex)
- ✅ Added comprehensive input validation (booking ID, reason, ticket, amount)
- ✅ Standardized error responses
- ✅ Added 58 unit tests (80%+ coverage)
- ✅ Structured refund policy (dict, not string)
- ✅ Added logging for audit trail
- ✅ Full documentation (README + docstrings)
- ✅ MCP 2.x compatibility

See `REVIEW_FINDINGS.md` for detailed issue list and roadmap.

## Debugging Tips

**When tests fail:**
1. Run with `-vv` for full diff: `pytest test_travelops_mcp_server.py::TestX -vv`
2. Add `--tb=long` to see full traceback
3. Check logs: add `logger.debug()` lines temporarily

**When server won't start:**
1. Check MCP version: `python -c "import mcp; print(mcp.__version__)"`
2. Verify venv activated: `which python` should show `.venv/bin/python`
3. Check imports: `python -c "from travelops_mcp_server import *"` (will error on first start if missing MCP)

**When tool returns unexpected response:**
1. Check validation logic in validate_* functions
2. Add temporary log statements: `logger.debug(f"Booking: {booking}")`
3. Run specific test: `pytest test_travelops_mcp_server.py::TestEstimateRefund -vv`

---

**Last Updated**: 2026-09-26  
**Status**: Phase 1 complete (Security & Validation hardened)  
**Next Work**: Phase 2 (Architecture refactor to modular structure)
