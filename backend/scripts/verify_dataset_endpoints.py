import urllib.request
import json

base = "http://127.0.0.1:8000/api/dataset"

endpoints = [
    f"{base}/overview",
    f"{base}/providers",
    f"{base}/statistics",
    f"{base}/benchmark",
    f"{base}/benchmark/history",
    f"{base}/samples?limit=5",
]

for ep in endpoints:
    try:
        req = urllib.request.Request(ep)
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read().decode('utf-8'))
            print(f"GET {ep} -> Status {r.status}, Keys: {list(data.keys()) if isinstance(data, dict) else len(data)}")
    except Exception as e:
        print(f"GET {ep} -> Error: {e}")

# Test POST /api/dataset/benchmark/run
try:
    req = urllib.request.Request(f"{base}/benchmark/run", data=b"", method="POST")
    with urllib.request.urlopen(req, timeout=10) as r:
        res = json.loads(r.read().decode('utf-8'))
        print(f"POST {base}/benchmark/run -> Status {r.status}, Benchmark ID: {res.get('benchmark_id')}, F1: {res.get('metrics', {}).get('f1')}")
except Exception as e:
    print(f"POST {base}/benchmark/run -> Error: {e}")
