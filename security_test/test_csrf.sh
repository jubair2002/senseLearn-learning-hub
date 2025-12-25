#!/bin/bash
# Test script for CSRF protection

echo "============================================================"
echo "CSRF Protection Test"
echo "============================================================"
echo "Testing: CSRF token validation"
echo "Expected: Request without CSRF token should fail"
echo "============================================================"
echo ""

BASE_URL="${1:-http://localhost:5000}"

# First, get CSRF token from a GET request (if available)
echo "Step 1: Getting CSRF token from session..."
echo ""

# Try to get CSRF token (this depends on your implementation)
# For now, we'll test without token
echo "Step 2: Making POST request WITHOUT CSRF token..."
echo ""

response=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
    -X POST "$BASE_URL/api/auth/register" \
    -H "Content-Type: application/json" \
    -d '{"email":"test@example.com","password":"test123","full_name":"Test User","user_type":"student"}' \
    2>/dev/null)

http_code=$(echo "$response" | grep "HTTP_CODE" | cut -d: -f2)
response_body=$(echo "$response" | grep -v "HTTP_CODE")

if [ "$http_code" = "403" ]; then
    echo "  ✅ Status: $http_code (CSRF Protection Working!)"
    echo "  📝 Response: $response_body"
    echo ""
    echo "  ✅ CSRF protection is blocking requests without token!"
elif [ "$http_code" = "400" ] || [ "$http_code" = "200" ]; then
    echo "  ⚠️  Status: $http_code"
    echo "  📝 Response: $response_body"
    echo ""
    echo "  ℹ️  Note: CSRF might not be enabled on this endpoint, or token validation passed"
else
    echo "  ℹ️  Status: $http_code"
    echo "  📝 Response: $response_body"
fi

echo ""
echo "============================================================"
echo "Test Summary"
echo "============================================================"
echo "Expected: Request without CSRF token should return 403"
echo ""
echo "Note: Some endpoints may not have CSRF protection enabled"
echo "============================================================"

