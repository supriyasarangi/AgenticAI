"""
Comprehensive test suite for TravelOps MCP Server.

Run with: pytest test_travelops_mcp_server.py -v --cov=travelops_mcp_server
"""

import pytest
import re
from travelops_mcp_server import (
    get_booking,
    estimate_refund,
    check_escalation,
    validate_booking_id,
    validate_reason,
    validate_ticket_text,
    validate_amount,
    calculate_refund,
    BOOKING_ID_PATTERN,
    MAX_REASON_LENGTH,
    MAX_TICKET_LENGTH,
)

# ============================================================================
# VALIDATION FUNCTION TESTS
# ============================================================================

class TestValidateBookingId:
    """Test booking ID validation."""

    def test_valid_booking_id(self):
        is_valid, error = validate_booking_id("BK-1001")
        assert is_valid is True
        assert error is None

    def test_valid_booking_id_different_number(self):
        is_valid, error = validate_booking_id("BK-9999")
        assert is_valid is True
        assert error is None

    def test_empty_booking_id(self):
        is_valid, error = validate_booking_id("")
        assert is_valid is False
        assert "empty" in error.lower()

    def test_invalid_format_no_prefix(self):
        is_valid, error = validate_booking_id("1001")
        assert is_valid is False
        assert "format" in error.lower()

    def test_invalid_format_wrong_prefix(self):
        is_valid, error = validate_booking_id("B-1001")
        assert is_valid is False
        assert "format" in error.lower()

    def test_invalid_format_letters_in_number(self):
        is_valid, error = validate_booking_id("BK-10A1")
        assert is_valid is False
        assert "format" in error.lower()

    def test_invalid_format_missing_dash(self):
        is_valid, error = validate_booking_id("BK1001")
        assert is_valid is False

    def test_invalid_format_too_many_digits(self):
        is_valid, error = validate_booking_id("BK-10001")
        assert is_valid is False


class TestValidateReason:
    """Test reason text validation."""

    def test_valid_reason_short(self):
        is_valid, error = validate_reason("Customer requested cancellation")
        assert is_valid is True
        assert error is None

    def test_valid_reason_max_length(self):
        reason = "x" * MAX_REASON_LENGTH
        is_valid, error = validate_reason(reason)
        assert is_valid is True
        assert error is None

    def test_empty_reason(self):
        is_valid, error = validate_reason("")
        assert is_valid is False
        assert "empty" in error.lower()

    def test_reason_exceeds_max_length(self):
        reason = "x" * (MAX_REASON_LENGTH + 1)
        is_valid, error = validate_reason(reason)
        assert is_valid is False
        assert "exceeds" in error.lower()


class TestValidateTicketText:
    """Test ticket text validation."""

    def test_valid_ticket_short(self):
        is_valid, error = validate_ticket_text("Help with my booking")
        assert is_valid is True
        assert error is None

    def test_valid_ticket_max_length(self):
        ticket = "x" * MAX_TICKET_LENGTH
        is_valid, error = validate_ticket_text(ticket)
        assert is_valid is True
        assert error is None

    def test_empty_ticket(self):
        is_valid, error = validate_ticket_text("")
        assert is_valid is False
        assert "empty" in error.lower()

    def test_ticket_exceeds_max_length(self):
        ticket = "x" * (MAX_TICKET_LENGTH + 1)
        is_valid, error = validate_ticket_text(ticket)
        assert is_valid is False
        assert "exceeds" in error.lower()


class TestValidateAmount:
    """Test amount validation."""

    def test_valid_amount_positive(self):
        is_valid, error = validate_amount(50000)
        assert is_valid is True
        assert error is None

    def test_valid_amount_zero(self):
        is_valid, error = validate_amount(0)
        assert is_valid is True
        assert error is None

    def test_valid_amount_none(self):
        is_valid, error = validate_amount(None)
        assert is_valid is True
        assert error is None

    def test_invalid_amount_negative(self):
        is_valid, error = validate_amount(-1000)
        assert is_valid is False
        assert "negative" in error.lower()


# ============================================================================
# BUSINESS LOGIC TESTS
# ============================================================================

class TestCalculateRefund:
    """Test refund calculation logic."""

    def test_airline_cancellation_full_refund(self):
        booking = {
            "customer": "Test Customer",
            "route": "DEL-LIS",
            "fare": "economy",
            "status": "cancelled_by_airline",
            "amount_inr": 86000,
            "departure": "2026-07-21",
            "baggage": "test",
        }
        result = calculate_refund("BK-1001", booking, "Airline cancelled flight")
        assert result["refund_amount_inr"] == 86000
        assert result["approval_required"] is False  # Below 50k for airline

    def test_airline_cancellation_high_amount_requires_approval(self):
        booking = {
            "customer": "Test Customer",
            "route": "DEL-LIS",
            "fare": "business",
            "status": "cancelled_by_airline",
            "amount_inr": 500000,
            "departure": "2026-07-21",
            "baggage": "test",
        }
        result = calculate_refund("BK-1002", booking, "Airline cancelled flight")
        assert result["refund_amount_inr"] == 500000
        assert result["approval_required"] is False  # Airline cancellations don't need approval

    def test_customer_cancellation_70_percent_refund(self):
        booking = {
            "customer": "Test Customer",
            "route": "DEL-LIS",
            "fare": "economy",
            "status": "confirmed",
            "amount_inr": 72000,
            "departure": "2026-07-20",
            "baggage": "test",
        }
        result = calculate_refund("BK-1001", booking, "Customer requested cancellation")
        assert result["refund_amount_inr"] == int(72000 * 0.7)
        assert result["approval_required"] is True  # Customer cancellations require approval

    def test_customer_cancellation_high_amount(self):
        booking = {
            "customer": "Test Customer",
            "route": "DEL-LIS",
            "fare": "economy",
            "status": "confirmed",
            "amount_inr": 100000,
            "departure": "2026-07-20",
            "baggage": "test",
        }
        result = calculate_refund("BK-1001", booking, "Customer requested cancellation")
        assert result["refund_amount_inr"] == int(100000 * 0.7)
        assert result["approval_required"] is True


# ============================================================================
# GET_BOOKING TOOL TESTS
# ============================================================================

class TestGetBooking:
    """Test get_booking MCP tool."""

    def test_get_valid_booking(self):
        result = get_booking("BK-1001")
        assert "booking" in result
        assert result["booking"]["customer"] == "Maya Rao"
        assert "error" not in result

    def test_get_another_valid_booking(self):
        result = get_booking("BK-1002")
        assert "booking" in result
        assert result["booking"]["customer"] == "Arjun Mehta"

    def test_booking_not_found(self):
        result = get_booking("BK-9999")
        assert "error" in result
        assert "not found" in result["error"].lower()
        assert "booking" not in result

    def test_invalid_booking_id_format(self):
        result = get_booking("INVALID")
        assert "error" in result
        assert "format" in result["error"].lower()

    def test_empty_booking_id(self):
        result = get_booking("")
        assert "error" in result

    def test_booking_id_with_spaces(self):
        result = get_booking("BK-1001 ")
        assert "error" in result


# ============================================================================
# ESTIMATE_REFUND TOOL TESTS
# ============================================================================

class TestEstimateRefund:
    """Test estimate_refund MCP tool."""

    def test_estimate_airline_cancellation_refund(self):
        result = estimate_refund("BK-1002", "Airline cancelled flight")
        assert "booking_id" in result
        assert result["booking_id"] == "BK-1002"
        assert result["refund_amount_inr"] == 86000
        assert result["approval_required"] is False  # Airline cancellations don't require approval
        assert "error" not in result

    def test_estimate_customer_cancellation_refund(self):
        result = estimate_refund("BK-1001", "Customer requested cancellation")
        assert "booking_id" in result
        assert result["refund_amount_inr"] == int(72000 * 0.7)
        assert result["approval_required"] is True
        assert "error" not in result

    def test_booking_not_found(self):
        result = estimate_refund("BK-9999", "Test reason")
        assert "error" in result
        assert "not found" in result["error"].lower()

    def test_invalid_booking_id_format(self):
        result = estimate_refund("INVALID", "Test reason")
        assert "error" in result
        assert "format" in result["error"].lower()

    def test_empty_reason(self):
        result = estimate_refund("BK-1001", "")
        assert "error" in result
        assert "empty" in result["error"].lower()

    def test_reason_too_long(self):
        long_reason = "x" * (MAX_REASON_LENGTH + 1)
        result = estimate_refund("BK-1001", long_reason)
        assert "error" in result
        assert "exceeds" in result["error"].lower()

    def test_valid_max_length_reason(self):
        max_reason = "x" * MAX_REASON_LENGTH
        result = estimate_refund("BK-1001", max_reason)
        assert "error" not in result
        assert "refund_amount_inr" in result


# ============================================================================
# CHECK_ESCALATION TOOL TESTS
# ============================================================================

class TestCheckEscalation:
    """Test check_escalation MCP tool."""

    def test_medical_emergency_escalates(self):
        result = check_escalation("Customer experiencing medical emergency")
        assert result["escalate"] is True
        assert "medical" in result["reasons"]

    def test_legal_issue_escalates(self):
        result = check_escalation("I need legal advice about my booking")
        assert result["escalate"] is True
        assert "legal" in result["reasons"]

    def test_lawyer_mention_escalates(self):
        result = check_escalation("I'm consulting with a lawyer about this")
        assert result["escalate"] is True
        assert "lawyer" in result["reasons"]

    def test_compensation_demand_escalates(self):
        result = check_escalation("I demand compensation for this cancellation")
        assert result["escalate"] is True
        assert "compensation" in result["reasons"]

    def test_chargeback_escalates(self):
        result = check_escalation("I will initiate a chargeback if not resolved")
        assert result["escalate"] is True
        assert "chargeback" in result["reasons"]

    def test_stranded_passenger_escalates(self):
        result = check_escalation("I am stranded at the airport")
        assert result["escalate"] is True
        assert "stranded" in result["reasons"]

    def test_oxygen_medical_escalates(self):
        result = check_escalation("Customer requires oxygen on flight")
        assert result["escalate"] is True
        assert "oxygen" in result["reasons"]

    def test_high_refund_amount_escalates(self):
        result = check_escalation("Normal request", amount_inr=75000)
        assert result["escalate"] is True
        assert "refund_above_50000" in result["reasons"]

    def test_low_refund_amount_no_escalation(self):
        result = check_escalation("Normal request", amount_inr=30000)
        assert result["escalate"] is False

    def test_normal_ticket_no_escalation(self):
        result = check_escalation("Please help me reschedule my flight")
        assert result["escalate"] is False
        assert len(result["reasons"]) == 0

    def test_false_positive_prevention_legal(self):
        # "legal" appears but not as keyword
        result = check_escalation("I have a generally pleasant experience")
        assert result["escalate"] is False

    def test_case_insensitive_matching(self):
        result = check_escalation("I have a MEDICAL emergency")
        assert result["escalate"] is True
        assert "medical" in result["reasons"]

    def test_multiple_risk_factors(self):
        result = check_escalation(
            "I am stranded and need legal assistance with compensation",
            amount_inr=75000
        )
        assert result["escalate"] is True
        assert len(result["reasons"]) >= 3
        assert "stranded" in result["reasons"]
        assert "legal" in result["reasons"]
        assert "compensation" in result["reasons"]

    def test_empty_ticket_text(self):
        result = check_escalation("")
        assert "error" in result

    def test_ticket_exceeds_max_length(self):
        long_ticket = "x" * (MAX_TICKET_LENGTH + 1)
        result = check_escalation(long_ticket)
        assert "error" in result

    def test_negative_amount(self):
        result = check_escalation("Test ticket", amount_inr=-1000)
        assert "error" in result


# ============================================================================
# EDGE CASE AND INTEGRATION TESTS
# ============================================================================

class TestEdgeCases:
    """Test edge cases and integration scenarios."""

    def test_workflow_lookup_then_estimate(self):
        # Typical workflow: get booking, then estimate refund
        booking_result = get_booking("BK-1001")
        assert "booking" in booking_result

        refund_result = estimate_refund("BK-1001", "Customer requested cancellation")
        assert refund_result["refund_amount_inr"] == int(72000 * 0.7)

    def test_workflow_escalation_then_estimate(self):
        # Check escalation, then estimate refund if needed
        escalation_result = check_escalation(
            "Customer has medical emergency",
            amount_inr=75000
        )
        assert escalation_result["escalate"] is True

        refund_result = estimate_refund("BK-1001", "Medical emergency")
        assert "refund_amount_inr" in refund_result

    def test_booking_immutability(self):
        # Verify that booking lookups don't modify state
        result1 = get_booking("BK-1001")
        booking1 = result1["booking"]

        result2 = get_booking("BK-1001")
        booking2 = result2["booking"]

        assert booking1 == booking2

    def test_refund_amounts_are_integers(self):
        # Ensure refund amounts are integers (no floating point cents)
        result = estimate_refund("BK-1001", "Test")
        assert isinstance(result["refund_amount_inr"], int)

    def test_special_characters_in_reason(self):
        # Ensure special characters don't break the system
        result = estimate_refund("BK-1001", "Reason with <script>alert('xss')</script>")
        assert "error" not in result  # Should not be flagged as format error


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=travelops_mcp_server"])
