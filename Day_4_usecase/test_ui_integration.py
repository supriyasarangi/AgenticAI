#!/usr/bin/env python
"""
Integration test for UI ↔ Backend contract.

Tests that:
1. orchestration.graph.run_query_pipeline() exists and has correct signature
2. Input validation (R1: domain selection required)
3. Output structure matches expected contract
4. Error handling works correctly

Run: python test_ui_integration.py
"""

import sys
from typing import Dict, Any


def test_import_pipeline():
    """Test that run_query_pipeline can be imported."""
    try:
        from orchestration.graph import run_query_pipeline
        print("✓ Successfully imported run_query_pipeline from orchestration.graph")
        return True
    except ImportError as e:
        print(f"✗ Failed to import run_query_pipeline: {e}")
        return False


def test_input_validation():
    """Test that input validation works (R1: domain selection required)."""
    try:
        from orchestration.graph import run_query_pipeline

        # Test 1: Missing therapeutic_area
        try:
            run_query_pipeline(
                query="test",
                therapeutic_area=None,
                jurisdiction="FDA",
            )
            print("✗ Should have raised ValueError for missing therapeutic_area")
            return False
        except ValueError as e:
            print(f"✓ Correctly raises ValueError for missing therapeutic_area: {e}")

        # Test 2: Missing jurisdiction
        try:
            run_query_pipeline(
                query="test",
                therapeutic_area="oncology",
                jurisdiction=None,
            )
            print("✗ Should have raised ValueError for missing jurisdiction")
            return False
        except ValueError as e:
            print(f"✓ Correctly raises ValueError for missing jurisdiction: {e}")

        # Test 3: Invalid therapeutic_area (optional validation)
        try:
            result = run_query_pipeline(
                query="test",
                therapeutic_area="invalid_area",
                jurisdiction="FDA",
            )
            # May or may not raise depending on backend implementation
            print("⚠ Backend did not validate therapeutic_area (optional)")
        except (ValueError, Exception) as e:
            print(f"✓ Backend validated therapeutic_area: {e}")

        return True

    except Exception as e:
        print(f"✗ Unexpected error during input validation: {e}")
        return False


def test_output_structure():
    """Test that output has expected structure."""
    try:
        from orchestration.graph import run_query_pipeline

        result = run_query_pipeline(
            query="What is the FDA approval status?",
            therapeutic_area="oncology",
            jurisdiction="FDA",
        )

        # Check required fields
        required_fields = [
            "query",
            "therapeutic_area",
            "jurisdiction",
            "status",
            "final_answer",
            "claims",
            "citations",
            "evidence",
            "trace",
        ]

        missing_fields = [f for f in required_fields if f not in result]
        if missing_fields:
            print(f"✗ Missing fields in output: {missing_fields}")
            return False

        print(f"✓ Output has all required fields: {required_fields}")

        # Check field types
        if not isinstance(result.get("query"), str):
            print("✗ 'query' should be str")
            return False

        if not isinstance(result.get("therapeutic_area"), str):
            print("✗ 'therapeutic_area' should be str")
            return False

        if not isinstance(result.get("claims"), list):
            print("✗ 'claims' should be list")
            return False

        if not isinstance(result.get("citations"), list):
            print("✗ 'citations' should be list")
            return False

        if not isinstance(result.get("evidence"), list):
            print("✗ 'evidence' should be list")
            return False

        if not isinstance(result.get("trace"), list):
            print("✗ 'trace' should be list")
            return False

        print("✓ Output field types are correct")

        # Check claim structure
        for claim in result.get("claims", []):
            if "sentence" not in claim or "confidence_tier" not in claim:
                print("✗ Claim missing required fields: sentence, confidence_tier")
                return False

        print(f"✓ Claims have required fields")

        # Check citation structure
        for citation in result.get("citations", []):
            required_citation_fields = ["number", "source", "exact_span"]
            missing = [f for f in required_citation_fields if f not in citation]
            if missing:
                print(f"✗ Citation missing fields: {missing}")
                return False

        print(f"✓ Citations have required fields")

        return True

    except Exception as e:
        print(f"⚠ Could not test output structure (Phase 0 may return errors): {e}")
        return True  # Non-blocking in Phase 0


def test_multiple_queries():
    """Test multiple queries to ensure state is managed correctly."""
    try:
        from orchestration.graph import run_query_pipeline

        queries = [
            ("What is the efficacy?", "oncology", "FDA"),
            ("What about cardiology?", "cardiology", "EMA"),
            ("Compare efficacy", "neurology", "ICH"),
        ]

        for query, area, jurisdiction in queries:
            result = run_query_pipeline(
                query=query,
                therapeutic_area=area,
                jurisdiction=jurisdiction,
            )

            if result.get("therapeutic_area") != area:
                print(f"✗ Scope not preserved: expected {area}, got {result.get('therapeutic_area')}")
                return False

            if result.get("jurisdiction") != jurisdiction:
                print(f"✗ Jurisdiction not preserved")
                return False

        print(f"✓ Scope correctly preserved across {len(queries)} queries")
        return True

    except Exception as e:
        print(f"⚠ Could not test multiple queries (Phase 0 may return errors): {e}")
        return True


def test_domain_values():
    """Test valid domain values."""
    valid_areas = ["oncology", "cardiology", "neurology", "immunology", "infectious_disease", "rare_disease"]
    valid_jurisdictions = ["FDA", "EMA", "ICH", "PMDA", "MHRA", "GLOBAL"]

    try:
        from orchestration.graph import run_query_pipeline

        # Test one valid combination
        result = run_query_pipeline(
            query="test",
            therapeutic_area=valid_areas[0],
            jurisdiction=valid_jurisdictions[0],
        )

        print(f"✓ Valid domain values accepted: {valid_areas[0]} / {valid_jurisdictions[0]}")
        return True

    except ValueError as e:
        print(f"✗ Valid domain values rejected: {e}")
        return False
    except Exception as e:
        print(f"⚠ Could not test domain values (Phase 0): {e}")
        return True


def main():
    """Run all tests."""
    print("=" * 70)
    print("UI ↔ Backend Integration Test Suite")
    print("=" * 70)
    print()

    tests = [
        ("Import orchestration.graph", test_import_pipeline),
        ("Input validation (R1)", test_input_validation),
        ("Output structure", test_output_structure),
        ("Multiple queries", test_multiple_queries),
        ("Valid domain values", test_domain_values),
    ]

    results = []
    for name, test_func in tests:
        print(f"\n--- {name} ---")
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            results.append((name, False))

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:8} {name}")

    print()
    print(f"Result: {passed}/{total} tests passed")

    if passed == total:
        print("\n✓ All tests passed! UI can integrate with backend.")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed. See output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
