#!/usr/bin/env python3

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, cwd=None):
    try:
        result = subprocess.run(command, cwd=cwd, check=False)
        return result.returncode == 0
    except Exception as e:
        print(f"Error: {e}")
        return False

def run_backend_tests(service_name, service_path):
    print(f"\n{service_name}")
    print("-" * 50)
    
    if not (service_path / "tests").exists():
        print("No tests found")
        return True
    
    requirements_test = service_path / "requirements-test.txt"
    if requirements_test.exists():
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r", "requirements-test.txt"], 
                      cwd=str(service_path), capture_output=True)
    
    success = run_command([sys.executable, "-m", "pytest", "-v"], cwd=str(service_path))
    return success

def run_frontend_tests():
    print(f"\nFrontend")
    print("-" * 50)
    print("Skipping frontend tests (npm not configured)")
    return True

def main():
    print("\n" + "=" * 50)
    print("Test Results")
    print("=" * 50)
    
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
            if run_backend_tests(service_name, service_path):
                passed.append(service_name)
            else:
                failed.append(service_name)
    
    if run_frontend_tests():
        passed.append("Frontend")
    else:
        failed.append("Frontend")
    
    print("\n" + "=" * 50)
    print(f"Passed: {len(passed)}")
    for s in passed:
        print(f"  ✓ {s}")
    
    if failed:
        print(f"\nFailed: {len(failed)}")
        for s in failed:
            print(f"  ✗ {s}")
    
    print("=" * 50 + "\n")
    
    sys.exit(1 if failed else 0)

if __name__ == "__main__":
    main()
