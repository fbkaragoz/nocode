#!/usr/bin/env python3
"""
Entry point for the Advanced Automatic Code Generation System.
Fixes import issues by setting up proper Python path.
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

# Now import and run the main application
from main import main

if __name__ == "__main__":
    sys.exit(main()) 