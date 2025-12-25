#!/bin/bash
# Test script for account lockout functionality

echo "============================================================"
echo "Account Lockout Test"
echo "============================================================"
echo "Testing: Account lockout after 5 failed login attempts"
echo "Expected: Account locked after 5 failed attempts"
echo "============================================================"
echo ""

BASE_URL="${1:-http://localhost:5000}"
LOGIN_URL="$BASE_URL/api/auth/login"

# Use a test email
TEST_EMAIL="lockout_test@example.com"

echo "Making 6 failed login attempts with email: $TEST_EMAIL"
echo ""

for i in {1..6}; do
    echo "Attempt $i:"
    response=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
        -X POST "$LOGIN_URL" \
        -H "Content-Type: application/json" \
        -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"wrongpassword\"}" \
        2>/dev/null)
    
    http_code=$(echo "$response" | grep "HTTP_CODE" | cut -d: -f2)
    response_body=$(echo "$response" | grep -v "HTTP_CODE")
    
    if [ "$http_code" = "423" ]; then
        echo "  🔒 Status: $http_code (Account Locked!)"
        echo "  📝 Response: $response_body"
        echo ""
        echo "  ✅ Account lockout is working!"
    elif [ "$http_code" = "401" ]; then
        # Try to extract remaining attempts if available
        remaining=$(echo "$response_body" | grep -o '"remaining_attempts":[0-9]*' | cut -d: -f2 || echo "N/A")
        echo "  ⚠️  Status: $http_code (Login Failed)"
        if [ "$remaining" != "N/A" ]; then
            echo "  📊 Remaining attempts: $remaining"
        fi
    else
        echo "  ℹ️  Status: $http_code"
    fi
    echo ""
    
    sleep 0.2
done

echo "============================================================"
echo "Test Summary"
echo "============================================================"
echo "Expected: After 5 failed attempts, 6th should return 423 (Locked)"
echo ""
echo "If you see 423 on attempt 6, account lockout is working! ✅"
echo "============================================================"

