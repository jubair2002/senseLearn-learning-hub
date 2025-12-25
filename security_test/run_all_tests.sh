#!/bin/bash
# Run all security tests

echo "============================================================"
echo "Running All Security Tests"
echo "============================================================"
echo ""

BASE_URL="${1:-http://localhost:5000}"

echo "⚠️  Make sure your Flask app is running at: $BASE_URL"
echo ""
read -p "Press Enter to continue or Ctrl+C to cancel..."
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "============================================================"
echo "Test 1: Rate Limiting"
echo "============================================================"
bash "$SCRIPT_DIR/test_rate_limiting.sh" "$BASE_URL"
echo ""
echo ""

echo "============================================================"
echo "Test 2: Account Lockout"
echo "============================================================"
bash "$SCRIPT_DIR/test_account_lockout.sh" "$BASE_URL"
echo ""
echo ""

echo "============================================================"
echo "Test 3: CSRF Protection"
echo "============================================================"
bash "$SCRIPT_DIR/test_csrf.sh" "$BASE_URL"
echo ""
echo ""

echo "============================================================"
echo "Test 4: Security Headers"
echo "============================================================"
bash "$SCRIPT_DIR/test_security_headers.sh" "$BASE_URL"
echo ""
echo ""

echo "============================================================"
echo "All Tests Complete!"
echo "============================================================"

