#!/bin/bash
# Test script for security headers

echo "============================================================"
echo "Security Headers Test"
echo "============================================================"
echo "Testing: Security HTTP headers in responses"
echo "============================================================"
echo ""

BASE_URL="${1:-http://localhost:5000}"

echo "Making request to check security headers..."
echo ""

response=$(curl -s -I "$BASE_URL/" 2>/dev/null)

echo "Security Headers Found:"
echo ""

# Check for various security headers
headers=(
    "Content-Security-Policy"
    "X-Content-Type-Options"
    "X-Frame-Options"
    "X-XSS-Protection"
    "Referrer-Policy"
    "Permissions-Policy"
    "Strict-Transport-Security"
)

found_count=0
for header in "${headers[@]}"; do
    value=$(echo "$response" | grep -i "$header" | cut -d: -f2- | sed 's/^[ \t]*//')
    if [ -n "$value" ]; then
        echo "  ✅ $header: $value"
        found_count=$((found_count + 1))
    else
        echo "  ❌ $header: Not found"
    fi
done

echo ""
echo "============================================================"
echo "Test Summary"
echo "============================================================"
echo "Found $found_count out of ${#headers[@]} security headers"
echo ""

if [ $found_count -ge 4 ]; then
    echo "✅ Good security headers coverage!"
elif [ $found_count -ge 2 ]; then
    echo "⚠️  Some security headers are missing"
else
    echo "❌ Most security headers are missing"
fi

echo "============================================================"

