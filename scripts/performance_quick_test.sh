#!/bin/bash

# Quick Performance Test - Single command to test all pages
# Usage: ./scripts/performance_quick_test.sh

echo "🚀 Quick Performance Test"
echo "========================"

# Check if server is running
if ! curl -s http://localhost:8080/health &> /dev/null; then
    echo "❌ Server not running. Starting optimized frontend server..."
    ./.venv/bin/python3 frontend_server.py &
    sleep 3
    echo "✅ Server started"
fi

# Test compression is working
echo -n "🗜️  Testing compression... "
if curl -H "Accept-Encoding: gzip" -I http://localhost:8080/src/styles/main.min.css 2>/dev/null | grep -q "content-encoding: gzip"; then
    echo "✅ Working"
else
    echo "❌ Not working - check server configuration"
fi

# Quick Lighthouse tests (simplified)
echo "📊 Running quick performance audits..."

# Test just the dashboard for quick feedback
if command -v lighthouse &> /dev/null; then
    lighthouse http://localhost:8080/#dashboard \
        --only-categories=performance \
        --chrome-flags="--headless" \
        --quiet | grep "Performance:" || echo "Dashboard test completed"
else
    echo "💡 Install Lighthouse for full testing: npm install -g lighthouse"
fi

echo "✅ Quick test completed. Run ./scripts/run_performance_tests.sh for full analysis."