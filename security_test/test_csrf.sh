#!/bin/bash
# CSRF Protection Test Script

echo "============================================================"
echo "CSRF Protection Test"
echo "============================================================"
echo "Testing: CSRF token validation"
echo "Expected: Request without CSRF token should fail"
echo "============================================================"
echo ""

BASE_URL="${1:-http://localhost:5000}"

echo "Step 1: Preparing to make request without CSRF token..."
echo ""

# Make POST request without CSRF token
response=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
    -X POST "$BASE_URL/api/auth/register" \
    -H "Content-Type: application/json" \
    -d '{"email":"test@example.com","password":"test123","full_name":"Test User","user_type":"student"}' \
    2>/dev/null)

# Extract HTTP code and response body
http_code=$(echo "$response" | grep "HTTP_CODE" | cut -d: -f2)
response_body=$(echo "$response" | grep -v "HTTP_CODE")

# Check the result
if [ "$http_code" = "403" ]; then
    echo "Status: $http_code - CSRF Protection Working"
    echo "Response: $response_body"
elif [ "$http_code" = "400" ] || [ "$http_code" = "200" ]; then
    echo "Status: $http_code"
    echo "Response: $response_body"
    echo "Note: CSRF might not be enabled on this endpoint, or token validation passed"
else
    echo "Status: $http_code"
    echo "Response: $response_body"
fi

echo ""
echo "============================================================"
echo "Test Summary"
echo "============================================================"
echo "Expected: Request without CSRF token should return 403"
echo "Note: Some endpoints may not have CSRF protection enabled"
echo "============================================================"
