import sys
import os

# Add the parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.examples.test_connections import test_all_connections, print_summary

if __name__ == "__main__":
    print("Starting database connection tests...")
    results = test_all_connections()
    print_summary(results)
    
    # Exit with status code 1 if any connection failed
    if not all(results.values()):
        sys.exit(1) 