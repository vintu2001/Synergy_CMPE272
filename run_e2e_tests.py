import subprocess
import sys
import os


def run_e2e_tests():
    print("=" * 80)
    print("RUNNING END-TO-END TESTS")
    print("=" * 80)
    print("\nPrerequisites:")
    print("- All services must be running on localhost:8001-8004")
    print("- Run: docker compose -f infrastructure/docker/docker-compose.microservices.yml up")
    print("\n" + "=" * 80 + "\n")
    
    test_dir = os.path.join(os.path.dirname(__file__), "tests")
    
    cmd = [
        sys.executable, "-m", "pytest",
        test_dir,
        "-v",
        "--tb=short",
        "-s"
    ]
    
    result = subprocess.run(cmd, cwd=os.path.dirname(__file__))
    
    print("\n" + "=" * 80)
    if result.returncode == 0:
        print("✅ All end-to-end tests PASSED")
    else:
        print("❌ Some end-to-end tests FAILED")
    print("=" * 80 + "\n")
    
    return result.returncode


if __name__ == "__main__":
    sys.exit(run_e2e_tests())
