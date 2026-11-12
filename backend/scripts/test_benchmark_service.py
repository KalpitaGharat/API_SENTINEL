import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.api_key_benchmark import ApiKeyBenchmarkService
import json

res = ApiKeyBenchmarkService.run_benchmark()
print("Benchmark ID:", res["benchmark_id"])
print("Total Samples Evaluated:", res["total_samples"])
print("Duration ms:", res["duration_ms"])
print("Metrics:", json.dumps(res["metrics"], indent=2))
print("Per-Provider Results:")
for p in res["per_provider"]:
    print(f"  {p['provider']:16}: Precision={p['precision']}%, Recall={p['recall']}%, F1={p['f1']}, Accuracy={p['accuracy']}%")
