#!/usr/bin/env python3
"""
Workflow runner - wrapper for lib/workflow.py
"""
import sys

# Add lib to path
sys.path.append("lib")

from workflow import main  # noqa: E402

if __name__ == "__main__":
    main()
