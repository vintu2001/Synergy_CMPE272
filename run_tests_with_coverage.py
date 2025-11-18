import subprocess
import sys
import os
from pathlib import Path


def run_service_tests_with_coverage(service_name, service_path):
    print(f"\n{'=' * 80}")
    print(f"Running tests with coverage: {service_name}")
    print('=' * 80)
    
    if not (service_path / "tests").exists():
        print("No tests found")
        return True
    
    requirements_test = service_path / "requirements-test.txt"
    if requirements_test.exists():
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-q", "-r", "requirements-test.txt"],
            cwd=str(service_path),
            capture_output=True
        )
    
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-q", "pytest-cov"],
        capture_output=True
    )
    
    app_dir = service_path / "app"
    if app_dir.exists():
        source_arg = f"--cov={app_dir.name}"
    else:
        source_arg = "--cov=."
    
    cmd = [
        sys.executable, "-m", "pytest",
        source_arg,
        "--cov-report=term-missing",
        "--cov-report=html:coverage_html",
        "--cov-report=json:coverage.json",
        "-v",
        "--tb=short"
    ]
    
    result = subprocess.run(cmd, cwd=str(service_path))
    
    coverage_html = service_path / "coverage_html"
    if coverage_html.exists():
        print(f"\n📊 Coverage report: {coverage_html / 'index.html'}")
    
    return result.returncode == 0


def run_e2e_tests_with_coverage():
    print(f"\n{'=' * 80}")
    print("Running E2E tests")
    print('=' * 80)
    
    test_dir = Path(__file__).parent / "tests"
    if not test_dir.exists():
        print("No E2E tests found")
        return True
    
    cmd = [
        sys.executable, "-m", "pytest",
        str(test_dir),
        "-v",
        "--tb=short"
    ]
    
    result = subprocess.run(cmd, cwd=str(Path(__file__).parent))
    
    return result.returncode == 0


def main():
    print("\n" + "=" * 80)
    print("TEST COVERAGE REPORT")
    print("=" * 80)
    
    os.chdir(Path(__file__).parent)
    
    passed = []
    failed = []
    
    services = [
        ("Request Management", Path("services/request-management")),
        ("AI Processing", Path("services/ai-processing")),
        ("Decision Simulation", Path("services/decision-simulation")),
        ("Execution", Path("services/execution"))
    ]
    
    for service_name, service_path in services:
        if service_path.exists():
            if run_service_tests_with_coverage(service_name, service_path):
                passed.append(service_name)
            else:
                failed.append(service_name)
    
    if run_e2e_tests_with_coverage():
        passed.append("E2E Tests")
    else:
        failed.append("E2E Tests")
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"✅ Passed: {len(passed)}")
    for s in passed:
        print(f"   {s}")
    
    if failed:
        print(f"\n❌ Failed: {len(failed)}")
        for s in failed:
            print(f"   {s}")
    
    print("\n" + "=" * 80)
    print("Coverage reports generated:")
    print("- services/*/coverage_html/index.html (HTML - unit tests)")
    print("- services/*/coverage.json (JSON - unit tests)")
    print("\nNote: E2E tests verify integration but don't measure code coverage")
    print("as they test running services, not importable modules.")
    print("=" * 80 + "\n")
    
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
