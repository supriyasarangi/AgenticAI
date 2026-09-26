# Phase 2: Architecture Refactor Plan

## Overview

**Goal**: Transform single-file MVP into modular, scalable architecture  
**Duration**: 3-5 days  
**Priority**: High (enables Phase 3: Database Integration)  
**Status**: Not started

---

## Current State (Phase 1)

```
travelops_mcp_server.py (400 lines)
├── Type definitions
├── Configuration
├── Validation functions
├── Business logic
├── MCP tools
├── MCP resources
└── MCP prompts
```

**Issues with current structure**:
- ❌ Single 400-line file (hard to maintain)
- ❌ Tight coupling (validation, logic, MCP interface mixed)
- ❌ No database abstraction (would need refactor to add DB)
- ❌ Difficult to test components independently
- ❌ Hard to add new features without touching core logic

---

## Target State (Phase 2)

```
travelops/
├── __init__.py
├── server.py (entry point, ~40 lines)
├── models.py (TypedDicts, ~50 lines)
├── database.py (Repository abstraction, ~80 lines)
├── business_logic.py (RefundCalculator, EscalationChecker, ~100 lines)
├── handlers.py (MCP tool implementations, ~150 lines)
├── config.py (Configuration, policies, ~50 lines)
└── logging_setup.py (Logging configuration, ~30 lines)

tests/
├── __init__.py
├── test_models.py
├── test_business_logic.py
├── test_database.py
├── test_handlers.py
└── fixtures.py

travelops_mcp_server.py (new entry point, ~20 lines)
```

---

## Detailed Tasks

### Task 1: Create Package Structure

**Subtasks**:
1. Create `travelops/` directory
2. Create `travelops/__init__.py`
3. Create `tests/` directory
4. Create `tests/__init__.py`
5. Create all module stubs

**Time**: 15 minutes  
**Output**: Empty module structure ready for implementation

```bash
mkdir -p travelops tests
touch travelops/__init__.py tests/__init__.py
touch travelops/{server,models,database,business_logic,handlers,config,logging_setup}.py
touch tests/{test_models,test_business_logic,test_database,test_handlers,fixtures}.py
```

---

### Task 2: Extract Type Definitions (models.py)

**Current code**: Lines 25-42 in travelops_mcp_server.py

**New file**: `travelops/models.py`

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

class ErrorResponse(TypedDict):
    error: str
    details: str

class RefundEstimate(TypedDict):
    booking_id: str
    refund_amount_inr: int
    approval_required: bool
    reason: str

class RefundPolicy(TypedDict):
    version: str
    airline_cancellation: dict
    customer_cancellation: dict
```

**Tests**: New file `tests/test_models.py`
- Verify TypedDict structure
- Test optional/required fields

**Time**: 20 minutes  
**Dependencies**: None

---

### Task 3: Extract Configuration (config.py)

**Current code**: Lines 48-85 in travelops_mcp_server.py

**New file**: `travelops/config.py`

```python
import re
from typing import Dict
import os

# Validation patterns
BOOKING_ID_PATTERN = r'^BK-\d{4}$'
MAX_REASON_LENGTH = int(os.getenv('MAX_REASON_LENGTH', '500'))
MAX_TICKET_LENGTH = int(os.getenv('MAX_TICKET_LENGTH', '10000'))

# Compiled patterns (computed once at startup)
ESCALATION_PATTERNS: Dict[str, re.Pattern] = {
    "medical": re.compile(r'\bmedical\b', re.IGNORECASE),
    "legal": re.compile(r'\blegal\b', re.IGNORECASE),
    # ... etc
}

# Refund policy (structure instead of string)
REFUND_POLICY_STRUCTURED = {
    "version": "3",
    "airline_cancellation": {...},
    "customer_cancellation": {...}
}

REFUND_POLICY_TEXT = """Helios Refund Policy v3..."""

# Load from environment
def load_policy_from_env() -> dict:
    """Load policy from external source in Phase 3."""
    return REFUND_POLICY_STRUCTURED
```

**Tests**: New file `tests/test_config.py`
- Verify patterns compile
- Test environment variable loading

**Time**: 20 minutes  
**Dependencies**: None

---

### Task 4: Create Database Abstraction (database.py)

**New file**: `travelops/database.py`

This is the key abstraction that enables database integration in Phase 3.

```python
from abc import ABC, abstractmethod
from typing import Optional, List
from models import BookingData

class BookingRepository(ABC):
    """Abstract repository for booking storage."""
    
    @abstractmethod
    def get_booking(self, booking_id: str) -> Optional[BookingData]:
        """Get booking by ID. Return None if not found."""
        pass
    
    @abstractmethod
    def list_bookings(self, customer_id: str = None) -> List[BookingData]:
        """List bookings, optionally filtered by customer."""
        pass

class InMemoryBookingRepository(BookingRepository):
    """In-memory implementation for testing."""
    
    def __init__(self, test_data: dict):
        self.bookings = test_data
    
    def get_booking(self, booking_id: str) -> Optional[BookingData]:
        return self.bookings.get(booking_id)
    
    def list_bookings(self, customer_id: str = None) -> List[BookingData]:
        if customer_id:
            return [b for b in self.bookings.values() if b.get('customer_id') == customer_id]
        return list(self.bookings.values())

class SQLBookingRepository(BookingRepository):
    """SQL database implementation (Phase 3)."""
    
    def __init__(self, db_url: str):
        self.engine = None  # sqlalchemy.create_engine(db_url)
        # Placeholder for Phase 3
    
    def get_booking(self, booking_id: str) -> Optional[BookingData]:
        # Phase 3: Query database
        pass
    
    def list_bookings(self, customer_id: str = None) -> List[BookingData]:
        # Phase 3: Query database
        pass
```

**Tests**: New file `tests/test_database.py`
- Test InMemoryBookingRepository with test data
- Verify interface implementation

**Time**: 40 minutes  
**Dependencies**: models.py

---

### Task 5: Extract Business Logic (business_logic.py)

**Current code**: Lines 150-179 in travelops_mcp_server.py

**New file**: `travelops/business_logic.py`

```python
from models import BookingData, RefundEstimate
from config import REFUND_POLICY_STRUCTURED, ESCALATION_PATTERNS
import logging

logger = logging.getLogger(__name__)

class RefundCalculator:
    """Encapsulates refund calculation logic."""
    
    def __init__(self, policy: dict):
        self.policy = policy
    
    def calculate(self, booking_id: str, booking: BookingData, reason: str) -> dict:
        """Calculate refund amount based on booking status."""
        # Current business logic from calculate_refund()
        pass

class EscalationChecker:
    """Encapsulates escalation detection logic."""
    
    def __init__(self, patterns: dict):
        self.patterns = patterns
    
    def check(self, ticket_text: str, amount_inr: int = None) -> dict:
        """Determine if ticket needs escalation."""
        # Current business logic from check_escalation()
        pass
```

**Tests**: New file `tests/test_business_logic.py`
- Test RefundCalculator with various scenarios
- Test EscalationChecker with risk patterns

**Time**: 40 minutes  
**Dependencies**: models.py, config.py, logging_setup.py

---

### Task 6: Create Handler Functions (handlers.py)

**Current code**: Lines 240-340 in travelops_mcp_server.py

**New file**: `travelops/handlers.py`

```python
from business_logic import RefundCalculator, EscalationChecker
from database import BookingRepository
from validators import validate_booking_id, validate_reason, validate_ticket_text

class ToolHandlers:
    """MCP tool implementations."""
    
    def __init__(self, 
                 booking_repo: BookingRepository,
                 refund_calc: RefundCalculator,
                 escalation_checker: EscalationChecker):
        self.booking_repo = booking_repo
        self.refund_calc = refund_calc
        self.escalation_checker = escalation_checker
    
    def get_booking(self, booking_id: str) -> dict:
        """Tool: Look up booking by ID."""
        is_valid, error = validate_booking_id(booking_id)
        if not is_valid:
            return {"error": error}
        
        booking = self.booking_repo.get_booking(booking_id)
        if not booking:
            return {"error": f"Booking not found: {booking_id}"}
        
        return {"booking": booking}
    
    # ... estimate_refund, check_escalation implementations
```

**Tests**: New file `tests/test_handlers.py`
- Mock BookingRepository, RefundCalculator, EscalationChecker
- Test each handler independently

**Time**: 60 minutes  
**Dependencies**: All of the above

---

### Task 7: Logging Setup (logging_setup.py)

**New file**: `travelops/logging_setup.py`

```python
import logging
import os
from logging.handlers import RotatingFileHandler

def configure_logging(log_level: str = None, log_file: str = None):
    """Configure logging for the application."""
    
    level = getattr(logging, log_level or os.getenv('LOG_LEVEL', 'INFO'))
    
    logger = logging.getLogger()
    logger.setLevel(level)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    
    # File handler (if specified)
    if log_file:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=100*1024*1024,  # 100MB
            backupCount=10
        )
        file_handler.setLevel(level)
        logger.addHandler(file_handler)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
```

**Time**: 20 minutes  
**Dependencies**: None

---

### Task 8: Create Entry Point (server.py)

**New file**: `travelops/server.py`

```python
import logging
from mcp.server.mcpserver import MCPServer
from database import InMemoryBookingRepository
from business_logic import RefundCalculator, EscalationChecker
from handlers import ToolHandlers
from config import REFUND_POLICY_STRUCTURED, ESCALATION_PATTERNS, BOOKINGS

logger = logging.getLogger(__name__)

def create_server():
    """Create and configure MCP server."""
    
    # Initialize dependencies
    booking_repo = InMemoryBookingRepository(BOOKINGS)
    refund_calc = RefundCalculator(REFUND_POLICY_STRUCTURED)
    escalation_checker = EscalationChecker(ESCALATION_PATTERNS)
    
    handlers = ToolHandlers(booking_repo, refund_calc, escalation_checker)
    
    # Create MCP server
    mcp = MCPServer("travelops")
    
    # Register tools
    @mcp.tool()
    def get_booking(booking_id: str) -> dict:
        return handlers.get_booking(booking_id)
    
    @mcp.tool()
    def estimate_refund(booking_id: str, reason: str) -> dict:
        return handlers.estimate_refund(booking_id, reason)
    
    @mcp.tool()
    def check_escalation(ticket_text: str, amount_inr: int = None) -> dict:
        return handlers.check_escalation(ticket_text, amount_inr)
    
    # Register resources
    @mcp.resource("travelops://policy/refund/text")
    def refund_policy() -> str:
        # Return policy text
        pass
    
    # Register prompts
    @mcp.prompt()
    def triage_travel_ticket(ticket_text: str) -> str:
        # Return prompt template
        pass
    
    return mcp

if __name__ == "__main__":
    from logging_setup import configure_logging
    configure_logging()
    
    mcp = create_server()
    logger.info("Starting TravelOps MCP Server")
    mcp.run()
```

**Time**: 30 minutes  
**Dependencies**: All modules

---

### Task 9: Update Entry Point (travelops_mcp_server.py)

**New file**: `travelops_mcp_server.py` (simplified)

```python
#!/usr/bin/env python3
"""TravelOps MCP Server - Entry point."""

import os
from travelops.server import create_server
from travelops.logging_setup import configure_logging

if __name__ == "__main__":
    configure_logging(
        log_level=os.getenv('LOG_LEVEL', 'INFO'),
        log_file=os.getenv('LOG_FILE')
    )
    
    mcp = create_server()
    mcp.run()
```

**Time**: 5 minutes

---

### Task 10: Migrate Tests

**Current**: `test_travelops_mcp_server.py` (works with monolithic file)  
**New**: Organized test modules

```
tests/
├── test_models.py (TypedDict validation)
├── test_business_logic.py (RefundCalculator, EscalationChecker)
├── test_database.py (Repository implementations)
├── test_handlers.py (Tool handlers with mocks)
├── test_integration.py (End-to-end workflows)
└── fixtures.py (Shared test data)
```

**Time**: 90 minutes  
**Process**:
1. Create test structure
2. Migrate existing tests to appropriate modules
3. Update imports
4. Run full test suite

---

## Implementation Order

**Day 1** (2-3 hours):
1. Task 1: Package structure (15 min)
2. Task 2: Extract models (20 min)
3. Task 3: Extract config (20 min)
4. Task 4: Database abstraction (40 min)

**Day 2** (3-4 hours):
5. Task 5: Business logic (40 min)
6. Task 6: Handlers (60 min)
7. Task 7: Logging setup (20 min)

**Day 3** (2-3 hours):
8. Task 8: Server (30 min)
9. Task 9: Entry point (5 min)
10. Task 10: Migrate tests (90 min)

**Day 4**: Testing, validation, bug fixes

---

## Testing Strategy

### Phase 2 Test Coverage

All tests should remain at 93%+ coverage:

```
travelops/models.py          → tests/test_models.py
travelops/config.py          → Inline tests
travelops/database.py        → tests/test_database.py
travelops/business_logic.py  → tests/test_business_logic.py
travelops/handlers.py        → tests/test_handlers.py (mocked deps)
tests/test_integration.py    → End-to-end workflows
```

### Test Execution

```bash
# Run all tests
pytest tests/ -v --cov=travelops --cov-report=html

# Run specific module tests
pytest tests/test_business_logic.py -v

# Run with coverage report
pytest tests/ --cov=travelops --cov-report=term-missing
```

---

## Benefits After Phase 2

✅ **Separation of Concerns**
- Models: Data structures only
- Config: Configuration only
- Database: Data access abstraction
- Business Logic: Pure functions, no MCP coupling
- Handlers: MCP interface only
- Logging: Centralized

✅ **Easier Testing**
- Test business logic without MCP
- Mock repositories for handler tests
- No need to import large modules

✅ **Ready for Phase 3**
- Can swap InMemoryBookingRepository for SQLBookingRepository
- No other code changes needed

✅ **Maintainability**
- Clear file responsibilities
- Easier to navigate
- Simpler to add features

---

## Rollback Plan

If Phase 2 encounters issues:

```bash
# Revert to Phase 1
git checkout v1.0.0-phase1
python travelops_mcp_server.py

# Phase 2 branch remains for debugging
git checkout phase2-refactor
# Fix issues
git push origin phase2-refactor
```

---

## Success Criteria

- [x] All modules created
- [x] All tests migrated
- [x] All 58 tests passing
- [x] Coverage maintained at 93%+
- [x] Local deployment still works
- [x] No functional changes to user-facing behavior
- [x] Code review passed
- [x] Git tag created (v1.1.0-phase2)

---

## Next Steps

1. **Review this plan** with team
2. **Get approval** to proceed
3. **Create branch**: `git checkout -b phase2-refactor`
4. **Follow task list** in order
5. **Commit incrementally** after each task
6. **Test continuously** - run pytest after each task
7. **Create PR** when complete
8. **Merge** to main after review

---

**Status**: Planning Complete  
**Ready to Start**: Yes  
**Estimated Time**: 3-5 days  
**Priority**: High (enables Phase 3)
