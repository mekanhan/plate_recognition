# Performance Testing & Optimization

This directory contains performance testing tools and documentation for the LPR application.

## Quick Start

### 🚀 Run Performance Tests
```bash
# Full performance audit of all pages
./scripts/run_performance_tests.sh

# Quick test (dashboard only)
./scripts/performance_quick_test.sh
```

### 📊 Current Performance Scores
- **Dashboard**: 74% (+17 from baseline)
- **Cameras**: 79% (+19 from baseline)  
- **Recording**: 57% (+7 from baseline)
- **Detections**: 73% (+16 from baseline)
- **Settings**: 73% (+15 from baseline)

**Average: 71% performance score**

## Files in this Directory

### Documentation
- `performance_optimization_guide.md` - Complete optimization guide
- `README.md` - This file

### Scripts  
- `../scripts/run_performance_tests.sh` - Full Lighthouse audit suite
- `../scripts/performance_quick_test.sh` - Quick performance check

### Reports
- `*_report_MMDDYYYY.json` - Lighthouse audit reports
- `performance_summary_MMDDYYYY.md` - Human-readable summaries

## Key Optimizations Applied

### ✅ Completed (August 2025)
1. **GZip Compression** - 75-84% file size reduction
2. **CSS Preloading** - Critical resources load first
3. **Resource Hints** - Preconnect to external domains
4. **Cache Optimization** - 1-year cache for static assets
5. **Duplicate Removal** - Fixed multiple CSS loading

### 🔄 Future Improvements
- Service Worker implementation
- Unused code removal (138KB potential savings)
- Critical CSS inlining
- WebP image conversion

## Running Tests

### Prerequisites
```bash
# Install Lighthouse
npm install -g lighthouse

# Install jq for JSON processing
sudo apt install jq  # Ubuntu/Debian
brew install jq      # macOS
```

### Manual Testing
```bash
# Test single page
lighthouse http://localhost:8080/#dashboard --output=json

# Test with specific options
lighthouse http://localhost:8080/#cameras \
    --output=json \
    --chrome-flags="--headless" \
    --throttling-method=devtools
```

### Automated Testing
```bash
# Run all tests and generate summary
./scripts/run_performance_tests.sh

# View latest summary
cat docs/performance/performance_summary_*.md | tail -n 50
```

## Performance Targets

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Performance Score | >75% | 71% avg | 🟡 Close |
| First Contentful Paint | <1.8s | 2-3s | 🟡 Close |
| Largest Contentful Paint | <2.5s | 4-6s | 🔴 Needs work |
| Cumulative Layout Shift | <0.1 | <0.05 | ✅ Good |

## Troubleshooting

### Common Issues

#### Tests Fail - Server Not Running
```bash
# Start the optimized server
./.venv/bin/python3 frontend_server.py
```

#### Compression Not Working
```bash
# Check compression headers
curl -H "Accept-Encoding: gzip" -I http://localhost:8080/src/styles/main.min.css

# Should show: content-encoding: gzip
```

#### Lighthouse Not Found
```bash
# Install globally
npm install -g lighthouse

# Or use via npx
npx lighthouse http://localhost:8080
```

## Monitoring

### Performance Regression Detection
```bash
# Compare with baseline
./scripts/performance_compare.sh baseline.json current.json
```

### Continuous Monitoring
Set up alerts for:
- Performance score drops below 70%
- LCP increases above 4s
- New render-blocking resources

---

**Last Updated**: August 26, 2025  
**Next Review**: September 26, 2025