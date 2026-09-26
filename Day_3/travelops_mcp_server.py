import re
import logging
from typing import TypedDict, Literal

try:
    # MCP 2.x
    from mcp.server.mcpserver import MCPServer
    mcp = MCPServer("travelops")
except ImportError:
    # MCP 1.x (fallback)
    from mcp.server.fastmcp import FastMCP
    mcp = FastMCP("travelops")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# TYPE DEFINITIONS
# ============================================================================

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

# ============================================================================
# CONFIGURATION & VALIDATION
# ============================================================================

BOOKING_ID_PATTERN = r'^BK-\d{4}$'
MAX_REASON_LENGTH = 500
MAX_TICKET_LENGTH = 10000

# Compiled regex patterns for escalation check (computed once at startup)
ESCALATION_PATTERNS = {
    "medical": re.compile(r'\bmedical\b', re.IGNORECASE),
    "legal": re.compile(r'\blegal\b', re.IGNORECASE),
    "lawyer": re.compile(r'\blawyer\b', re.IGNORECASE),
    "compensation": re.compile(r'\bcompensation\b', re.IGNORECASE),
    "chargeback": re.compile(r'\bchargeback\b', re.IGNORECASE),
    "stranded": re.compile(r'\bstranded\b', re.IGNORECASE),
    "oxygen": re.compile(r'\boxygen\b', re.IGNORECASE),
}

# Refund policy as structured data (instead of string)
REFUND_POLICY_STRUCTURED = {
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
    }
}

REFUND_POLICY_TEXT = """
Helios Refund Policy v3
- Airline-cancelled trips are eligible for full refund.
- Customer-requested cancellations may include fare-rule charges.
- Refunds above INR 50,000 require human approval.
- Medical emergency, legal threat, chargeback, compensation demand, or unclear identity must be escalated.
- The support AI may estimate a refund but must not issue money without approval.
""".strip()

# ============================================================================
# TEST DATA (EXTRACTED & MARKED AS TEST-ONLY)
# ============================================================================

BOOKINGS = {
    "BK-1001": {
        "customer": "Maya Rao",
        "route": "DEL-LIS",
        "fare": "economy",
        "status": "confirmed",
        "amount_inr": 72000,
        "departure": "2026-07-20",
        "baggage": "1 cabin bag + 1 checked bag up to 23 kg",
    },
    "BK-1002": {
        "customer": "Arjun Mehta",
        "route": "DEL-LIS",
        "fare": "economy",
        "status": "cancelled_by_airline",
        "amount_inr": 86000,
        "departure": "2026-07-21",
        "baggage": "1 cabin bag + 1 checked bag up to 23 kg",
    },
}

# ============================================================================
# VALIDATION HELPERS
# ============================================================================

def validate_booking_id(booking_id: str) -> tuple[bool, str | None]:
    """Validate booking ID format and return (is_valid, error_message)."""
    if not booking_id:
        return False, "Booking ID cannot be empty"
    if not re.match(BOOKING_ID_PATTERN, booking_id):
        return False, f"Booking ID must match format BK-#### (got: {booking_id})"
    return True, None

def validate_reason(reason: str) -> tuple[bool, str | None]:
    """Validate reason text and return (is_valid, error_message)."""
    if not reason:
        return False, "Reason cannot be empty"
    if len(reason) > MAX_REASON_LENGTH:
        return False, f"Reason exceeds maximum length of {MAX_REASON_LENGTH} characters"
    return True, None

def validate_ticket_text(ticket_text: str) -> tuple[bool, str | None]:
    """Validate ticket text and return (is_valid, error_message)."""
    if not ticket_text:
        return False, "Ticket text cannot be empty"
    if len(ticket_text) > MAX_TICKET_LENGTH:
        return False, f"Ticket text exceeds maximum length of {MAX_TICKET_LENGTH} characters"
    return True, None

def validate_amount(amount_inr: int | None) -> tuple[bool, str | None]:
    """Validate amount and return (is_valid, error_message)."""
    if amount_inr is not None and amount_inr < 0:
        return False, "Amount cannot be negative"
    return True, None

# ============================================================================
# BUSINESS LOGIC
# ============================================================================

def calculate_refund(booking_id: str, booking: BookingData, reason: str) -> dict:
    """Calculate refund amount based on booking status and reason."""
    policy = REFUND_POLICY_STRUCTURED

    if booking["status"] == "cancelled_by_airline":
        refund_rate = policy["airline_cancellation"]["refund_rate"]
        threshold = policy["airline_cancellation"]["approval_threshold_inr"]
        requires_approval = (
            policy["airline_cancellation"]["requires_approval"] and
            (threshold is None or booking["amount_inr"] > threshold)
        )
    else:
        refund_rate = policy["customer_cancellation"]["refund_rate"]
        threshold = policy["customer_cancellation"]["approval_threshold_inr"]
        requires_approval = (
            policy["customer_cancellation"]["requires_approval"] and
            (threshold is None or booking["amount_inr"] > threshold)
        )

    refund_amount = int(booking["amount_inr"] * refund_rate)

    logger.info(
        f"Refund calculated for {booking['customer']}",
        extra={
            "booking_id": booking_id,
            "refund_rate": refund_rate,
            "refund_amount_inr": refund_amount,
            "requires_approval": requires_approval
        }
    )

    return {
        "refund_amount_inr": refund_amount,
        "approval_required": requires_approval
    }

# ============================================================================
# MCP TOOLS
# ============================================================================

@mcp.tool()
def get_booking(booking_id: str) -> dict:
    """
    Look up one booking by booking ID. Read-only.
    Use this before refund or customer response decisions.
    Does not modify booking state and does not expose payment card details.

    Args:
        booking_id: Booking identifier (format: BK-####)

    Returns:
        dict with keys:
        - 'booking': BookingData object if found
        - 'error': error message if not found or invalid format
    """
    # Validate input
    is_valid, error_msg = validate_booking_id(booking_id)
    if not is_valid:
        logger.warning(f"Invalid booking ID format: {booking_id}")
        return {"error": error_msg}

    # Lookup booking
    booking = BOOKINGS.get(booking_id)
    if not booking:
        logger.warning(f"Booking not found: {booking_id}")
        return {"error": f"Booking not found: {booking_id}"}

    logger.info(f"Booking retrieved: {booking_id} for {booking['customer']}")
    return {"booking": booking}

@mcp.tool()
def estimate_refund(booking_id: str, reason: str) -> dict:
    """
    Estimate refund amount for one booking. Calculation-only, not a payment action.
    Use only after get_booking confirms the booking exists.
    Returns approval_required=true when refund amount crosses policy threshold.

    Args:
        booking_id: Booking identifier (format: BK-####)
        reason: Cancellation reason (max 500 chars)

    Returns:
        dict with keys:
        - 'refund_amount_inr': calculated refund amount
        - 'approval_required': whether human approval is needed
        - 'reason': the cancellation reason
        - 'error': error message if validation fails
    """
    # Validate inputs
    is_valid, error_msg = validate_booking_id(booking_id)
    if not is_valid:
        logger.warning(f"Invalid booking ID in refund estimate: {booking_id}")
        return {"error": error_msg}

    is_valid, error_msg = validate_reason(reason)
    if not is_valid:
        logger.warning(f"Invalid reason in refund estimate: {error_msg}")
        return {"error": error_msg}

    # Lookup booking
    booking = BOOKINGS.get(booking_id)
    if not booking:
        logger.warning(f"Booking not found in refund estimate: {booking_id}")
        return {"error": f"Booking not found: {booking_id}"}

    # Calculate refund
    refund_info = calculate_refund(booking_id, booking, reason)

    return {
        "booking_id": booking_id,
        "refund_amount_inr": refund_info["refund_amount_inr"],
        "approval_required": refund_info["approval_required"],
        "reason": reason
    }

@mcp.tool()
def check_escalation(ticket_text: str, amount_inr: int | None = None) -> dict:
    """
    Check whether a ticket must be escalated to a human.
    Read-only risk classification. Does not contact the customer and does not change state.

    Uses word-boundary aware regex matching to detect escalation triggers:
    - Medical emergencies (medical, oxygen)
    - Legal issues (legal, lawyer)
    - Financial disputes (compensation, chargeback)
    - Stranded passengers
    - High refund amounts (> 50,000 INR)

    Args:
        ticket_text: Support ticket content (max 10,000 chars)
        amount_inr: Refund amount in INR (optional)

    Returns:
        dict with keys:
        - 'escalate': bool indicating if escalation is needed
        - 'reasons': list of escalation trigger terms
        - 'error': error message if validation fails
    """
    # Validate inputs
    is_valid, error_msg = validate_ticket_text(ticket_text)
    if not is_valid:
        logger.warning(f"Invalid ticket text: {error_msg}")
        return {"error": error_msg}

    is_valid, error_msg = validate_amount(amount_inr)
    if not is_valid:
        logger.warning(f"Invalid amount in escalation check: {error_msg}")
        return {"error": error_msg}

    # Scan for risk patterns (O(n) - single pass)
    reasons = []
    for term, pattern in ESCALATION_PATTERNS.items():
        if pattern.search(ticket_text):
            reasons.append(term)

    # Check high refund amount
    if amount_inr is not None and amount_inr > 50000:
        reasons.append("refund_above_50000")

    should_escalate = bool(reasons)

    if should_escalate:
        logger.warning(
            f"Ticket flagged for escalation",
            extra={"reasons": reasons, "amount_inr": amount_inr}
        )

    return {
        "escalate": should_escalate,
        "reasons": reasons
    }

# ============================================================================
# MCP RESOURCES
# ============================================================================

@mcp.resource("travelops://policy/refund/text")
def refund_policy() -> str:
    """Return the current Helios Travel refund and escalation policy as human-readable text."""
    return REFUND_POLICY_TEXT

@mcp.resource("travelops://policy/refund/structured")
def refund_policy_structured() -> dict:
    """Return the current Helios Travel refund policy as structured JSON."""
    return REFUND_POLICY_STRUCTURED

# ============================================================================
# MCP PROMPTS
# ============================================================================

@mcp.prompt()
def triage_travel_ticket(ticket_text: str) -> str:
    """
    Reusable triage prompt for Helios Travel support tickets.

    Args:
        ticket_text: The customer support ticket content

    Returns:
        Formatted prompt for triaging the ticket
    """
    return f"""
You are a Helios Travel support triage assistant.
Use the connected travelops MCP tools when booking, refund, or escalation facts are needed.

Your task:
1. Identify the customer's issue
2. Check if the issue requires escalation using check_escalation()
3. If safe to process, use get_booking() to retrieve booking details
4. Use estimate_refund() to calculate potential refund if applicable
5. Provide a customer-safe response and escalation recommendation

Support ticket:
{ticket_text}

Guidelines:
- Safety first: escalate any medical, legal, or high-value issues
- Be empathetic and transparent about refund calculations
- Provide booking details only when necessary
- Suggest next steps clearly
""".strip()

# ============================================================================
# SERVER STARTUP
# ============================================================================

if __name__ == "__main__":
    logger.info("Starting TravelOps MCP Server")
    logger.info(f"Loaded {len(BOOKINGS)} test bookings")
    logger.info(f"Using refund policy version {REFUND_POLICY_STRUCTURED['version']}")
    mcp.run()
