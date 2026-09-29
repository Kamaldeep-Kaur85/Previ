"""
app/benchmark.py

Real, hardware-grounded benchmark command for PreView AI.
Can be run via:
    python -m app.benchmark

Directives:
- Never fakes NPU execution or performance metrics.
- Uses QNN Execution Provider if Qualcomm Snapdragon hardware/QNN EP is present.
- Uses ONNX Runtime CPU Execution Provider fallback otherwise.
- Accurately measures warmup (10 runs) and benchmark iterations (100 runs).
- Reports Device, CPU, Backend, Model, Average, P50, and P95 latency.
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import List

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np

from app.ai.backend import detect_device_info, detect_available_providers, create_best_backend
from app.ai.model_builder import create_impact_predictor_onnx


def run_benchmark(iterations: int = 100, warmup_runs: int = 10):
    dev_info = detect_device_info()
    providers = detect_available_providers()

    model_dir = PROJECT_ROOT / "models"
    model_path = model_dir / "preview_impact_predictor.onnx"

    if not model_path.exists():
        model_dir.mkdir(parents=True, exist_ok=True)
        create_impact_predictor_onnx(model_path)

    model_size_kb = model_path.stat().st_size / 1024.0

    backend = create_best_backend()
    backend.load(model_path)
    session = backend.session

    input_name = session.get_inputs()[0].name
    # Create realistic input candidate vector: batch of 5 files, 16 features each
    test_features = np.array([
        [1.0, 1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.8, 3.0, 0.0, 0.0, 1.0, 0.0, 0.5, 0.2],
        [2.0, 0.0, 1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.4, 1.0, 0.0, 0.0, 0.0, 1.0, 0.2, 0.1],
        [1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.9, 5.0, 1.0, 0.0, 0.0, 0.0, 0.7, 0.3],
        [3.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.1, 0.0, 0.0, 0.0, 0.0, 0.0, 0.1, 0.0],
        [2.0, 0.0, 1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.5, 2.0, 0.0, 1.0, 0.0, 0.0, 0.4, 0.2],
    ], dtype=np.float32)

    # 1. Warmup runs
    for _ in range(warmup_runs):
        _ = session.run(None, {input_name: test_features})

    # 2. Measured benchmark runs
    latencies_ms: List[float] = []
    t_start_total = time.perf_counter()

    for _ in range(iterations):
        t0 = time.perf_counter()
        _ = session.run(None, {input_name: test_features})
        t1 = time.perf_counter()
        latencies_ms.append((t1 - t0) * 1000.0)

    t_end_total = time.perf_counter()
    total_time_s = t_end_total - t_start_total

    latencies_ms.sort()
    avg_latency = float(np.mean(latencies_ms))
    p50_latency = float(np.percentile(latencies_ms, 50))
    p95_latency = float(np.percentile(latencies_ms, 95))
    throughput = (iterations * len(test_features)) / total_time_s

    # Print formatted output matching specification
    print("=================================")
    print("PREVIEW AI BENCHMARK")
    print("=================================")
    print()
    print(f"Device:\n{dev_info['device']}")
    print()
    print(f"CPU:\n{dev_info['machine']} ({dev_info['os']})")
    print()
    print(f"Backend:\n{backend.backend_name} ({backend.accelerator_name})")
    print()
    print(f"Model:\n{model_path.name} ({model_size_kb:.1f} KB)")
    print()
    print("Warmup:")
    print(f"{warmup_runs} runs")
    print()
    print("Measured:")
    print(f"{iterations} runs")
    print()
    print("Average:")
    print(f"{avg_latency:.2f} ms")
    print()
    print("P50:")
    print(f"{p50_latency:.2f} ms")
    print()
    print("P95:")
    print(f"{p95_latency:.2f} ms")
    print()
    print("Throughput:")
    print(f"{throughput:.1f} inferences/sec")
    print("=================================")

    return {
        "device": dev_info["device"],
        "backend": backend.backend_name,
        "accelerator": backend.accelerator_name,
        "model": model_path.name,
        "average_ms": avg_latency,
        "p50_ms": p50_latency,
        "p95_ms": p95_latency,
        "throughput": throughput,
    }


if __name__ == "__main__":
    run_benchmark()
