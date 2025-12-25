#!/bin/bash
# Test script to check login API response format

echo "============================================================"
echo "Testing Login API Response Format"
echo "============================================================"
echo ""

BASE_URL="${1:-http://localhost:5000}"
LOGIN_URL="$BASE_URL/api/auth/login"

echo "Making login attempts to check response format..."
echo ""

for i in {1..3}; do
    echo "Attempt $i:"
    response=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
        -X POST "$LOGIN_URL" \
        -H "Content-Type: application/json" \
        -d '{"email":"test@example.com","password":"wrongpassword"}' \
        2>/dev/null)
    
    http_code=$(echo "$response" | grep "HTTP_CODE" | cut -d: -f2)
    response_body=$(echo "$response" | grep -v "HTTP_CODE")
    
    echo "  Status: $http_code"
    echo "  Response:"
    echo "$response_body" | python3 -m json.tool 2>/dev/null || echo "$response_body"
    echo ""
    
    sleep 0.5
done

echo "============================================================"
echo "Check if response includes:"
echo "  - failed_attempts"
echo "  - max_attempts"
echo "  - remaining_attempts"
echo "============================================================"

