#!/bin/bash
# Test script for rate limiting functionality

set -eu

BASE_URL="${1:-http://localhost:5000}"
LOGIN_URL="$BASE_URL/api/auth/login"

REQUESTS=6
EXPECTED_LIMIT=5

echo "============================================================"
echo "Rate Limiting Test"
echo "============================================================"
echo "Endpoint: POST /api/auth/login"
echo "Expected limit: $EXPECTED_LIMIT requests"
echo "============================================================"
echo ""

rate_limited=false

for i in $(seq 1 "$REQUESTS"); do
    echo "Request $i:"

    response=$(curl -s -w "\nHTTP_CODE:%{http_code}\nTIME:%{time_total}" \
        -X POST "$LOGIN_URL" \
        -H "Content-Type: application/json" \
        -d '{"email":"test@example.com","password":"wrongpassword"}' \
        -D "headers_$i.txt")

    http_code=$(echo "$response" | grep HTTP_CODE | cut -d: -f2)
    time_total=$(echo "$response" | grep TIME | cut -d: -f2)

    rate_limit=$(grep -i X-RateLimit-Limit headers_$i.txt | cut -d: -f2 | tr -d ' \r\n' || echo "N/A")
    rate_remaining=$(grep -i X-RateLimit-Remaining headers_$i.txt | cut -d: -f2 | tr -d ' \r\n' || echo "N/A")
    rate_reset=$(grep -i X-RateLimit-Reset headers_$i.txt | cut -d: -f2 | tr -d ' \r\n' || echo "N/A")

    if [ "$http_code" = "429" ]; then
        rate_limited=true
        echo "  Status: 429 (Rate limited)"
    else
        echo "  Status: $http_code"
    fi

    echo "  Response time: ${time_total}s"
    echo "  Rate limit headers:"
    echo "    Limit: ${rate_limit:-N/A}"
    echo "    Remaining: ${rate_remaining:-N/A}"
    echo "    Reset: ${rate_reset:-N/A}"
    echo ""

    sleep 0.1
done

rm -f headers_*.txt

echo "============================================================"
echo "Test Summary"
echo "============================================================"

if $rate_limited; then
    echo "Rate limiting is working (HTTP 429 detected)"
    exit 0
else
    echo "Rate limiting not detected"
    exit 1
fi
