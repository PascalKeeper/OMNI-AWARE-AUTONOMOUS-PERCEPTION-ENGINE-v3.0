"""Run all safety validation tests."""
import subprocess
import sys

tests = [
    "tests/test_v1_port.py",
    "tests/test_v094_port.py",
    "tests/test_v120_gold.py",
    "tests/test_grok_client.py",
    "tests/test_pipeline.py",
]

failed = 0
for t in tests:
    print(f"Running {t}...")
    r = subprocess.run([sys.executable, t], capture_output=True, text=True)
    print(r.stdout)
    if r.returncode != 0:
        print(r.stderr)
        failed += 1

print(f"\n{len(tests) - failed}/{len(tests)} test suites passed")
sys.exit(1 if failed else 0)