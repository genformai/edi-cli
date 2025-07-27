#!/usr/bin/env python3
"""Restore original project files after PyPI publishing."""

import shutil
from pathlib import Path

def main():
    """Restore original files."""
    print("🔄 Restoring original project files...")
    
    restore_files = {
        "pyproject_original.toml": "pyproject.toml", 
        "README_original.md": "README.md"
    }
    
    for backup, original in restore_files.items():
        if Path(backup).exists():
            shutil.copy2(backup, original)
            print(f"✅ Restored {original}")
            Path(backup).unlink()
            print(f"🗑️ Removed {backup}")
    
    print("✅ Restoration complete!")

if __name__ == "__main__":
    main()
