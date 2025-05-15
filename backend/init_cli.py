#!/usr/bin/env python

import sys
import argparse
from core.database import initialize_account

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initialize MVEditor Universe account (create required files).")
    parser.add_argument("--connection", default="default", help="Database connection name (default: default)")
    args = parser.parse_args()
    try:
        initialize_account(args.connection)
        print("Universe account initialized (or already set up).")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1) 