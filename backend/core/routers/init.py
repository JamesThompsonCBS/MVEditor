from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from ..database import initialize_account

router = APIRouter(tags=["init"])

@router.post("/init", response_model=Dict[str, Any])
async def init_account(connection_name: str = "default"):
    """Initialize the Universe account (create required MVEditor files) if they do not exist."""
    try:
        initialize_account(connection_name)
        return {"status": "success", "message": "Universe account initialized (or already set up)."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize Universe account: {str(e)}")

# CLI script (init_cli.py) in backend folder
"""
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
""" 