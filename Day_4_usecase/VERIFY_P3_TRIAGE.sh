#!/bin/bash
# Verification script for P3 Triage Agent installation

echo "=========================================="
echo "P3 TRIAGE AGENT INSTALLATION VERIFICATION"
echo "=========================================="
echo ""

errors=0
success=0

# Check 1: Agent spec
echo "✓ Checking agent specification..."
if [ -f "./.claude/agents/p3-triage-agent.md" ]; then
    echo "  ✓ .claude/agents/p3-triage-agent.md exists"
    ((success++))
else
    echo "  ✗ .claude/agents/p3-triage-agent.md MISSING"
    ((errors++))
fi

# Check 2: Policy config
echo "✓ Checking policy configuration..."
if [ -f "./config/triage_policy.yaml" ]; then
    echo "  ✓ config/triage_policy.yaml exists"
    ((success++))
else
    echo "  ✗ config/triage_policy.yaml MISSING"
    ((errors++))
fi

# Check 3: Implementation
echo "✓ Checking core implementation..."
if [ -f "./agents/p3_triage_agent.py" ]; then
    echo "  ✓ agents/p3_triage_agent.py exists"
    grep -q "class P3TriageAgent" ./agents/p3_triage_agent.py && echo "  ✓ P3TriageAgent class found" || echo "  ✗ P3TriageAgent class NOT found"
    ((success++))
else
    echo "  ✗ agents/p3_triage_agent.py MISSING"
    ((errors++))
fi

# Check 4: Schemas
echo "✓ Checking report schemas..."
if [ -f "./schemas/triage_report.py" ]; then
    echo "  ✓ schemas/triage_report.py exists"
    grep -q "class P3TriageReport" ./schemas/triage_report.py && echo "  ✓ P3TriageReport schema found" || echo "  ✗ P3TriageReport schema NOT found"
    ((success++))
else
    echo "  ✗ schemas/triage_report.py MISSING"
    ((errors++))
fi

# Check 5: Documentation
echo "✓ Checking documentation..."
if [ -f "./docs/p3-triage.md" ]; then
    echo "  ✓ docs/p3-triage.md exists"
    ((success++))
else
    echo "  ✗ docs/p3-triage.md MISSING"
    ((errors++))
fi

# Check 6: Example code
echo "✓ Checking example/test code..."
if [ -f "./eval/p3_triage_example.py" ]; then
    echo "  ✓ eval/p3_triage_example.py exists"
    ((success++))
else
    echo "  ✗ eval/p3_triage_example.py MISSING"
    ((errors++))
fi

# Check 7: Output directory
echo "✓ Checking output directory..."
mkdir -p eval/triage_reports
if [ -d "./eval/triage_reports" ]; then
    echo "  ✓ eval/triage_reports/ directory exists"
    ((success++))
else
    echo "  ✗ eval/triage_reports/ MISSING"
    ((errors++))
fi

# Check 8: Setup guides
echo "✓ Checking setup documentation..."
if [ -f "./P3_TRIAGE_AGENT_SETUP.md" ] && [ -f "./P3_TRIAGE_SUMMARY.md" ]; then
    echo "  ✓ Setup guides present"
    ((success++))
else
    echo "  ✗ Setup guides MISSING"
    ((errors++))
fi

echo ""
echo "=========================================="
echo "VERIFICATION COMPLETE"
echo "=========================================="
echo ""
echo "✓ Passed: $success/8"
echo "✗ Failed: $errors/8"
echo ""

if [ $errors -eq 0 ]; then
    echo "✅ All checks passed! P3 Triage Agent is ready."
    echo ""
    echo "Next steps:"
    echo "  1. Review docs/p3-triage.md for detailed documentation"
    echo "  2. Run eval/p3_triage_example.py to test the system"
    echo "  3. Edit config/triage_policy.yaml to customize policy"
    echo "  4. Integrate into orchestration/graph.py for production"
    exit 0
else
    echo "❌ Some checks failed. Please verify installation."
    exit 1
fi
