#!/usr/bin/env python3
"""
Load environment variables from .env file
"""

import os
from typing import Optional

def load_env_file(filepath: Optional[str] = None) -> None:
    """
    Load environment variables from a .env file.
    
    Args:
        filepath: Path to the .env file. If None, looks for .env in current directory.
    """
    if filepath is None:
        filepath = os.path.join(os.getcwd(), ".env")
    
    if not os.path.exists(filepath):
        return
    
    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    os.environ[key] = value

# Load environment variables when this module is imported
load_env_file()