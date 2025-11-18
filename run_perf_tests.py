import subprocess
import sys
from pathlib import Path


def run_performance_tests(service_name, service_path):
    """Run performance tests for a specific service"""
    print(f"\n{'='*80}")
    print(f"Running Performance Tests: {service_name}")
    print(f"{'='*80}\n")
    
    # Convert to absolute path
    base_dir = Path(__file__).parent
    service_abs_path = base_dir / service_path
    tests_path = service_abs_path / "tests"
    
    if not tests_path.exists():
        print(f"Tests directory not found: {tests_path}")
        return True
    
    perf_tests = list(tests_path.glob("perf_test_*.py"))
    
    if not perf_tests:
        print(f"No performance tests found in {tests_path}")
        return True
    
    # Run pytest on performance test files
    cmd = [
        sys.executable, "-m", "pytest",
        "-v",
        "--color=yes"
    ] + [str(f) for f in perf_tests]
    
    result = subprocess.run(cmd, cwd=str(service_abs_path))
    return result.returncode == 0


def run_load_tests(service_name, service_path, host, users=10, spawn_rate=2, duration="30s"):
    """Run Locust load tests for a service"""
    print(f"\n{'='*80}")
    print(f"Running Load Tests: {service_name}")
    print(f"Host: {host}")
    print(f"Users: {users}, Spawn Rate: {spawn_rate}, Duration: {duration}")
    print(f"{'='*80}\n")
    
    # Convert to absolute path
    base_dir = Path(__file__).parent
    service_abs_path = base_dir / service_path
    tests_path = service_abs_path / "tests"
    locustfile = tests_path / "locustfile.py"
    
    if not locustfile.exists():
        print(f"No locustfile found in {tests_path}")
        return True
    
    # Run Locust in headless mode
    cmd = [
        sys.executable, "-m", "locust",
        "-f", str(locustfile),
        "--host", host,
        "--users", str(users),
        "--spawn-rate", str(spawn_rate),
        "--run-time", duration,
        "--headless",
        "--only-summary"
    ]
    
    result = subprocess.run(cmd, cwd=tests_path)
    return result.returncode == 0


def main():
    """Run all performance tests"""
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║         SYNERGY PERFORMANCE TEST SUITE                        ║
    ║  Comprehensive performance testing for all microservices      ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)
    
    services = [
        {
            "name": "Request Management",
            "path": "services/request-management",
            "host": "http://localhost:8001"
        },
        {
            "name": "AI Processing",
            "path": "services/ai-processing",
            "host": "http://localhost:8002"
        },
        {
            "name": "Decision Simulation",
            "path": "services/decision-simulation",
            "host": "http://localhost:8003"
        },
        {
            "name": "Execution",
            "path": "services/execution",
            "host": "http://localhost:8004"
        }
    ]
    
    all_passed = True
    
    # Run pytest performance tests
    print("\n" + "="*80)
    print("PHASE 1: Code-Level Performance Tests (pytest-benchmark)")
    print("="*80)
    
    for service in services:
        passed = run_performance_tests(service["name"], service["path"])
        if not passed:
            all_passed = False
            print(f"❌ Performance tests failed for {service['name']}")
        else:
            print(f"✅ Performance tests passed for {service['name']}")
    
    # Ask user if they want to run load tests
    print("\n" + "="*80)
    print("PHASE 2: Load Testing (Locust)")
    print("="*80)
    print("\nNOTE: Load tests require services to be running!")
    print("Start services with: docker compose -f infrastructure/docker/docker-compose.microservices.yml up")
    
    try:
        response = input("\nRun load tests? (y/n): ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print("\nSkipping load tests")
        response = 'n'
    
    if response == 'y':
        # Get load test parameters
        try:
            users = int(input("Number of concurrent users (default: 10): ") or "10")
            spawn_rate = int(input("Spawn rate (users/sec, default: 2): ") or "2")
            duration = input("Duration (e.g., 30s, 1m, default: 30s): ") or "30s"
        except ValueError:
            print("Invalid input, using defaults")
            users = 10
            spawn_rate = 2
            duration = "30s"
        
        for service in services:
            passed = run_load_tests(
                service["name"],
                service["path"],
                service["host"],
                users,
                spawn_rate,
                duration
            )
            if not passed:
                all_passed = False
                print(f"❌ Load tests failed for {service['name']}")
            else:
                print(f"✅ Load tests passed for {service['name']}")
    else:
        print("\nSkipping load tests")
    
    # Final summary
    print("\n" + "="*80)
    print("PERFORMANCE TEST SUMMARY")
    print("="*80)
    
    if all_passed:
        print("✅ All performance tests PASSED")
        return 0
    else:
        print("❌ Some performance tests FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
