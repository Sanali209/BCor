import pytest
import sys

class ErrorCollector:
    def __init__(self):
        self.errors = []

    def pytest_collectreport(self, report):
        if report.failed:
            self.errors.append(report)

if __name__ == "__main__":
    collector = ErrorCollector()
    pytest.main(["--collect-only", "-v", "-p", "no:terminal"], plugins=[collector])
    
    print(f"\n--- Found {len(collector.errors)} collection errors ---\n")
    for err in collector.errors:
        print(f"File: {err.nodeid}")
        print(err.longrepr)
        print("-" * 40)
