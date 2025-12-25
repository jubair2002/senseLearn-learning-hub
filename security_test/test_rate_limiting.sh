#!/bin/bash
# Test script for rate limiting functionality

echo "============================================================"
echo "Rate Limiting Test"
echo "============================================================"
echo "Testing: POST /api/auth/login"
echo "Expected: 5 requests per 60 seconds"
echo "============================================================"
echo ""

BASE_URL="${1:-http://localhost:5000}"
LOGIN_URL="$BASE_URL/api/auth/login"

echo "Making 6 requests quickly..."
echo ""

for i in {1..6}; do
    echo "Request $i:"
    response=$(curl -s -w "\nHTTP_CODE:%{http_code}\nTIME:%{time_total}" \
        -X POST "$LOGIN_URL" \
        -H "Content-Type: application/json" \
        -d '{"email":"test@example.com","password":"wrongpassword"}' \
        -D headers_$i.txt 2>/dev/null)
    
    http_code=$(echo "$response" | grep "HTTP_CODE" | cut -d: -f2)
    time_total=$(echo "$response" | grep "TIME" | cut -d: -f2)
    
    # Extract rate limit headers
    rate_limit=$(grep -i "X-RateLimit-Limit" headers_$i.txt 2>/dev/null | cut -d: -f2 | tr -d ' \r\n' || echo "N/A")
    rate_remaining=$(grep -i "X-RateLimit-Remaining" headers_$i.txt 2>/dev/null | cut -d: -f2 | tr -d ' \r\n' || echo "N/A")
    rate_reset=$(grep -i "X-RateLimit-Reset" headers_$i.txt 2>/dev/null | cut -d: -f2 | tr -d ' \r\n' || echo "N/A")
    
    # Extract response message
    response_body=$(echo "$response" | grep -v "HTTP_CODE" | grep -v "TIME" | head -n -2)
    
    if [ "$http_code" = "429" ]; then
        echo "  🚫 Status: $http_code (Rate Limited!)"
        echo "  ⏰ Time: ${time_total}s"
        echo "  📊 Rate Limit Headers:"
        echo "     X-RateLimit-Limit: $rate_limit"
        echo "     X-RateLimit-Remaining: $rate_remaining"
        echo "     X-RateLimit-Reset: $rate_reset"
        echo "  📝 Response: $response_body"
    else
        echo "  ✅ Status: $http_code"
        echo "  ⏰ Time: ${time_total}s"
        echo "  📊 Rate Limit Headers:"
        echo "     X-RateLimit-Limit: $rate_limit"
        echo "     X-RateLimit-Remaining: $rate_remaining"
        echo "     X-RateLimit-Reset: $rate_reset"
    fi
    echo ""
    
    sleep 0.1
done

# Cleanup
rm -f headers_*.txt

echo "============================================================"
echo "Test Summary"
echo "============================================================"
echo "Expected: Request 6 should return 429 (Rate Limited)"
echo ""
echo "If you see 429 on request 6, rate limiting is working! ✅"
echo "============================================================"

