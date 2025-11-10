"""
run_tests.py - Test Runner Script

Convenience script to run all tests in the test suite.
"""

import sys
from pathlib import Path


# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

import importlib


test_10hour_scenario = importlib.import_module("test-10hour-scenario")
test_10hour = test_10hour_scenario.main


def run_all_tests():
    """Run all test scenarios"""
    print("\n" + "=" * 60)
    print(" " * 20 + "TEST SUITE")
    print("=" * 60)

    tests = [("10-Hour Scenario Test", test_10hour)]

    results = []

    for test_name, test_func in tests:
        print(f"\nRunning: {test_name}")
        print("-" * 60)

        try:
            exit_code = test_func()
            results.append((test_name, exit_code == 0))
        except Exception as e:
            print(f"ERROR: {test_name} crashed with exception:")
            print(f"  {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 60)
    print(" " * 20 + "TEST SUMMARY")
    print("=" * 60)

    for test_name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} {test_name}")

    all_passed = all(passed for _, passed in results)

    print("=" * 60)

    if all_passed:
        print("[PASS] ALL TESTS PASSED")
        return 0
    print("[FAIL] SOME TESTS FAILED")
    return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
