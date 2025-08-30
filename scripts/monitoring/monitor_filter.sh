#!/bin/bash
echo "Monitoring Detection Filter Performance..."
echo "=========================================="
for i in 1 2 3 4 5; do
    stats=$(curl -s http://localhost:8001/api/filter/stats)
    processed=$(echo $stats | python3 -c "import json,sys; print(json.load(sys.stdin)['total_processed'])")
    stored=$(echo $stats | python3 -c "import json,sys; print(json.load(sys.stdin)['stored'])")
    filtered=$(echo $stats | python3 -c "import json,sys; print(json.load(sys.stdin)['ignored_duplicates'])")
    rate=$(echo $stats | python3 -c "import json,sys; print(json.load(sys.stdin)['reduction_rate'])")
    echo "Sample $i: Processed=$processed, Stored=$stored, Filtered=$filtered, Reduction=$rate%"
    sleep 10
done
echo "=========================================="
echo "Final stats:"
curl -s http://localhost:8001/api/filter/stats | python3 -m json.tool