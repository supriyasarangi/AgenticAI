# TravelOps MCP Server

A Model Context Protocol (MCP) server for Helios Travel operations support, enabling AI-powered ticket triage, refund estimation, and escalation detection.

## Quick Start

### Setup

```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Run the Server

```bash
python travelops_mcp_server.py
```

The server will start listening on stdio (standard input/output) for MCP protocol connections.

### Run Tests

```bash
# Run all tests
pytest test_travelops_mcp_server.py -v

# Run with coverage report
pytest test_travelops_mcp_server.py -v --cov=travelops_mcp_server --cov-report=html

# Run specific test class
pytest test_travelops_mcp_server.py::TestGetBooking -v
```

## Architecture

```
travelops_mcp_server.py
├── Type Definitions (BookingData, ErrorResponse, etc.)
├── Configuration (patterns, policies, test data)
├── Validation Functions (booking ID, reason, ticket text, amount)
├── Business Logic (refund calculation)
├── MCP Tools (get_booking, estimate_refund, check_escalation)
├── MCP Resources (refund policy in text and JSON formats)
├── MCP Prompts (ticket triage template)
└── Server Startup
```

## MCP Tools

### 1. `get_booking(booking_id: str)`

Look up a booking by ID.

**Parameters:**
- `booking_id`: Booking identifier in format `BK-####` (e.g., "BK-1001")

**Returns:**
- On success: `{"booking": {...}}`
- On error: `{"error": "error message"}`

**Example:**
```python
result = get_booking("BK-1001")
# => {
#   "booking": {
#     "customer": "Maya Rao",
#     "route": "DEL-LIS",
#     "fare": "economy",
#     "status": "confirmed",
#     "amount_inr": 72000,
#     "departure": "2026-07-20",
#     "baggage": "1 cabin bag + 1 checked bag up to 23 kg"
#   }
# }
```

### 2. `estimate_refund(booking_id: str, reason: str)`

Calculate refund amount for a booking based on cancellation reason.

**Parameters:**
- `booking_id`: Booking identifier in format `BK-####`
- `reason`: Cancellation reason (max 500 characters)

**Returns:**
- On success:
  ```python
  {
    "booking_id": "BK-1001",
    "refund_amount_inr": 50400,
    "approval_required": true,
    "reason": "Customer requested cancellation"
  }
  ```
- On error: `{"error": "error message"}`

**Policy:**
- **Airline cancellations**: 100% refund (no approval needed if < 50k INR)
- **Customer cancellations**: 70% refund (always requires human approval if > 50k INR)

### 3. `check_escalation(ticket_text: str, amount_inr: int | None = None)`

Determine if a ticket requires escalation to human support.

**Parameters:**
- `ticket_text`: Support ticket content (max 10,000 characters)
- `amount_inr`: Refund amount in INR (optional)

**Returns:**
```python
{
  "escalate": true,
  "reasons": ["medical", "refund_above_50000"]
}
```

**Escalation Triggers:**
- Medical emergencies (keywords: medical, oxygen)
- Legal issues (keywords: legal, lawyer)
- Financial disputes (keywords: compensation, chargeback)
- Stranded passengers (keyword: stranded)
- High refund amounts (> 50,000 INR)

## MCP Resources

### 1. `travelops://policy/refund/text`

Returns the refund policy as human-readable text.

```
Helios Refund Policy v3
- Airline-cancelled trips are eligible for full refund.
- Customer-requested cancellations may include fare-rule charges.
- Refunds above INR 50,000 require human approval.
- Medical emergency, legal threat, chargeback, compensation demand, or unclear identity must be escalated.
- The support AI may estimate a refund but must not issue money without approval.
```

### 2. `travelops://policy/refund/structured`

Returns the refund policy as structured JSON.

```json
{
  "version": "3",
  "airline_cancellation": {
    "refund_rate": 1.0,
    "requires_approval": false,
    "approval_threshold_inr": null
  },
  "customer_cancellation": {
    "refund_rate": 0.7,
    "requires_approval": true,
    "approval_threshold_inr": 50000
  }
}
```

## MCP Prompts

### `triage_travel_ticket(ticket_text: str)`

A reusable prompt template for triaging customer support tickets.

**Usage:**
```
Apply the triage_travel_ticket prompt with customer support text to:
1. Identify the customer's issue
2. Check escalation requirements
3. Retrieve booking details if safe
4. Calculate refund estimates if applicable
5. Draft customer response
```

## Configuration

### Environment Variables

```bash
LOG_LEVEL=INFO          # Logging level (DEBUG, INFO, WARNING, ERROR)
DATABASE_URL=           # Future: database connection string
REFUND_POLICY_VERSION=3 # Policy version
MCP_TIMEOUT=30          # MCP timeout in seconds
```

### .mcp.json

The `.mcp.json` file configures this MCP server for connection:

```json
{
  "mcpServers": {
    "travelops": {
      "type": "stdio",
      "command": ".venv/bin/python",
      "args": ["travelops_mcp_server.py"]
    }
  }
}
```

## Test Coverage

The project includes comprehensive tests covering:

- **Validation Functions**: Input format validation, length limits, edge cases
- **Business Logic**: Refund calculations, policy application
- **MCP Tools**: Happy paths, error cases, boundary conditions
- **Edge Cases**: Integration workflows, state immutability, type checking

**Current Coverage Target**: 80%+ line coverage, 100% branch coverage for tools

### Test Categories

1. **Validation Tests** (`TestValidate*`): Input validation logic
2. **Business Logic Tests** (`TestCalculateRefund`): Refund calculations
3. **Tool Tests** (`TestGetBooking`, `TestEstimateRefund`, `TestCheckEscalation`): MCP tool behavior
4. **Edge Cases** (`TestEdgeCases`): Integration scenarios and corner cases

## Known Limitations

### Current (MVP)

- ✅ In-memory test data only (2 bookings)
- ✅ No database integration
- ✅ No authentication/authorization
- ✅ Synchronous processing only
- ✅ No audit logging to persistent storage

### Planned Improvements

- Database integration (PostgreSQL/SQLite)
- Persistent audit logging
- Batch refund processing
- Webhook notifications
- Rate limiting
- API authentication
- Distributed tracing

## Security

### Validation

- ✅ Booking ID format validation (regex: `^BK-\d{4}$`)
- ✅ Reason text length limits (max 500 chars)
- ✅ Ticket text length limits (max 10,000 chars)
- ✅ Refund amount validation (no negatives)

### Escalation Detection

- ✅ Word-boundary aware regex matching (prevents false positives)
- ✅ Case-insensitive pattern matching
- ✅ Multiple escalation factors aggregation

### Error Handling

- ✅ Consistent error response format
- ✅ Non-leaking error messages
- ✅ Validation before processing

## Logging

The server logs all significant operations:

```python
# Tool invocations
logger.info(f"Booking retrieved: {booking_id} for {customer_name}")

# Refund calculations
logger.info(f"Refund calculated for {customer}",
    extra={"booking_id": booking_id, "amount_inr": amount, ...})

# Escalations
logger.warning(f"Ticket flagged for escalation",
    extra={"reasons": reasons, "amount_inr": amount})

# Validation errors
logger.warning(f"Invalid booking ID format: {booking_id}")
```

View logs at the console or configure file logging via `logging.basicConfig()`.

## Troubleshooting

### Server won't start

```bash
# Check Python version
python --version  # Requires Python 3.10+

# Verify MCP installation
pip list | grep mcp

# Check for port conflicts
lsof -i :8000  # (if using network socket)
```

### Import errors

```bash
# Reinstall dependencies
pip install --force-reinstall -r requirements.txt

# Verify virtual environment activation
which python  # Should show .venv/bin/python
```

### Tests failing

```bash
# Run with verbose output
pytest test_travelops_mcp_server.py -vv

# Run specific test
pytest test_travelops_mcp_server.py::TestGetBooking::test_valid_booking_id -vv

# Check test coverage
pytest test_travelops_mcp_server.py --cov=travelops_mcp_server --cov-report=term-missing
```

## Development

### Adding a New Tool

1. Define validation function if needed
2. Add tool function decorated with `@mcp.tool()`
3. Add comprehensive tests in `test_travelops_mcp_server.py`
4. Update README documentation
5. Run full test suite: `pytest -v --cov`

### Adding a New Resource

1. Create resource function decorated with `@mcp.resource("travelops://...")`
2. Document in README
3. Add tests if applicable

### Code Style

- Follow PEP 8
- Type hints on all functions
- Docstrings for public functions
- Comprehensive error handling
- Logging for significant operations

## Future Roadmap

### Phase 1: Database Integration
- PostgreSQL backend
- Booking persistence
- Transaction support

### Phase 2: Advanced Features
- Multi-step refund workflows
- Batch processing
- Webhooks for notifications
- Compliance reporting

### Phase 3: Enterprise
- API authentication (OAuth2/JWT)
- Role-based access control
- Audit logging to compliant storage
- Rate limiting
- Distributed tracing

## Contributing

1. Create feature branch: `git checkout -b feature/my-feature`
2. Add tests for any new functionality
3. Ensure all tests pass: `pytest -v --cov`
4. Commit with clear messages
5. Push and create pull request

## Support

For issues or questions:
1. Check the Troubleshooting section
2. Review test cases for usage examples
3. Check logs: `LOG_LEVEL=DEBUG python travelops_mcp_server.py`

## License

Internal Helios Travel project.

---

**Last Updated**: 2026-09-26  
**Refactoring Status**: Phase 1 Complete (Security & Validation)
