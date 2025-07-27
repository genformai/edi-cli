#!/usr/bin/env python3
"""
Script to prepare and publish edi-cli to PyPI.

This script:
1. Backs up the current project files
2. Sets up the correct PyPI package structure
3. Builds the distribution
4. Provides instructions for publishing

Run this script from the project root directory.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

def run_command(cmd, check=True):
    """Run a shell command and print output."""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.stdout:
        print("STDOUT:", result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    if check and result.returncode != 0:
        print(f"Command failed with return code {result.returncode}")
        sys.exit(1)
    
    return result

def main():
    """Main function to prepare for PyPI publishing."""
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    print("🚀 Preparing edi-cli for PyPI publication...")
    print(f"📁 Working directory: {project_root}")
    
    # Step 1: Backup original files
    print("\n📋 Step 1: Backing up original files...")
    
    backup_files = {
        "pyproject.toml": "pyproject_original.toml",
        "README.md": "README_original.md"
    }
    
    for original, backup in backup_files.items():
        if Path(original).exists():
            shutil.copy2(original, backup)
            print(f"✅ Backed up {original} to {backup}")
    
    # Step 2: Set up PyPI files
    print("\n📦 Step 2: Setting up PyPI package structure...")
    
    # Copy PyPI-specific files
    if Path("pyproject_pypi.toml").exists():
        shutil.copy2("pyproject_pypi.toml", "pyproject.toml")
        print("✅ Copied pyproject_pypi.toml to pyproject.toml")
    
    if Path("README_PYPI.md").exists():
        shutil.copy2("README_PYPI.md", "README.md")
        print("✅ Copied README_PYPI.md to README.md")
    
    # Verify package structure
    required_files = ["edi_cli/__init__.py", "edi_cli/cli.py", "pyproject.toml", "README.md", "LICENSE"]
    
    print("\n🔍 Verifying package structure...")
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - MISSING!")
            return False
    
    # Step 3: Clean previous builds
    print("\n🧹 Step 3: Cleaning previous builds...")
    
    dirs_to_clean = ["build", "dist", "*.egg-info"]
    for pattern in dirs_to_clean:
        for path in Path(".").glob(pattern):
            if path.is_dir():
                shutil.rmtree(path)
                print(f"✅ Removed {path}")
    
    # Step 4: Install build dependencies
    print("\n📥 Step 4: Installing build dependencies...")
    
    try:
        run_command("python -m pip install --upgrade build twine")
        print("✅ Build dependencies installed")
    except:
        print("❌ Failed to install build dependencies")
        return False
    
    # Step 5: Build the package
    print("\n🔨 Step 5: Building the package...")
    
    try:
        run_command("python -m build")
        print("✅ Package built successfully")
    except:
        print("❌ Package build failed")
        return False
    
    # Step 6: Verify the build
    print("\n🔍 Step 6: Verifying the build...")
    
    dist_files = list(Path("dist").glob("*"))
    if len(dist_files) >= 2:  # Should have both .whl and .tar.gz
        print("✅ Build artifacts created:")
        for file_path in dist_files:
            print(f"   📦 {file_path}")
    else:
        print("❌ Build verification failed - missing artifacts")
        return False
    
    # Step 7: Test the package
    print("\n🧪 Step 7: Testing the package locally...")
    
    try:
        # Check if the package can be imported
        run_command("python -c \"import edi_cli; print('✅ Package imports successfully')\"")
        
        # Test the CLI entry point
        run_command("python -m edi_cli.cli", check=False)
        
        print("✅ Package testing completed")
    except:
        print("⚠️ Package testing had issues, but continuing...")
    
    # Step 8: Provide publishing instructions
    print("\n🚀 Step 8: Ready for publishing!")
    print("\n" + "="*60)
    print("📋 NEXT STEPS FOR PUBLISHING:")
    print("="*60)
    print()
    print("1. 🔐 Set up PyPI authentication:")
    print("   - Create account at https://pypi.org/")
    print("   - Generate API token at https://pypi.org/manage/account/token/")
    print("   - Configure: python -m twine configure")
    print()
    print("2. 🧪 Test upload to Test PyPI (recommended first):")
    print("   python -m twine upload --repository testpypi dist/*")
    print()
    print("3. 🌟 Upload to PyPI:")
    print("   python -m twine upload dist/*")
    print()
    print("4. ✅ Test installation:")
    print("   pip install edi-cli")
    print("   edi-cli")
    print()
    print("5. 🔄 Restore original files after publishing:")
    print("   python restore_files.py")
    print()
    print("="*60)
    print("📦 Package is ready for publication!")
    print("="*60)
    
    # Create restore script
    restore_script = '''#!/usr/bin/env python3
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
'''
    
    with open("restore_files.py", "w") as f:
        f.write(restore_script)
    
    print("📄 Created restore_files.py for cleanup after publishing")
    
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 Preparation completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Preparation failed!")
        sys.exit(1)