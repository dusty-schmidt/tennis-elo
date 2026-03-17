#!/usr/bin/env python3
"""Version management script for Tennis ELO

Usage:
    python scripts/bump_version.py major  # Bump major version (1.0.0 -> 2.0.0)
    python scripts/bump_version.py minor  # Bump minor version (1.0.0 -> 1.1.0)
    python scripts/bump_version.py patch  # Bump patch version (1.0.0 -> 1.0.1)
    python scripts/bump_version.py show   # Show current version
"""
import sys
import re
from pathlib import Path

def get_current_version():
    """Get current version from __init__.py"""
    init_file = Path("src/tennis_elo/__init__.py")
    content = init_file.read_text()
    match = re.search(r'__version__ = "([\d\.]+)"', content)
    if match:
        return match.group(1)
    raise ValueError("Version not found in __init__.py")

def bump_version(version, bump_type):
    """Bump version based on type"""
    major, minor, patch = map(int, version.split('.'))
    
    if bump_type == 'major':
        major += 1
        minor = 0
        patch = 0
    elif bump_type == 'minor':
        minor += 1
        patch = 0
    elif bump_type == 'patch':
        patch += 1
    else:
        raise ValueError(f"Invalid bump type: {bump_type}")
    
    return f"{major}.{minor}.{patch}"

def update_files(old_version, new_version):
    """Update version in all relevant files"""
    files = {
        'src/tennis_elo/__init__.py': (r'__version__ = "[\d\.]+"', f'__version__ = "{new_version}"'),
        'pyproject.toml': (r'version = "[\d\.]+"', f'version = "{new_version}"'),
    }
    
    for filepath, (pattern, replacement) in files.items():
        content = Path(filepath).read_text()
        content = re.sub(pattern, replacement, content)
        Path(filepath).write_text(content)
        print(f"✓ Updated {filepath}")

def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    
    bump_type = sys.argv[1].lower()
    
    if bump_type == 'show':
        version = get_current_version()
        print(f"Current version: {version}")
        return
    
    if bump_type not in ['major', 'minor', 'patch']:
        print(f"Error: Invalid bump type '{bump_type}'")
        print("Use: major, minor, or patch")
        sys.exit(1)
    
    current = get_current_version()
    new = bump_version(current, bump_type)
    
    print(f"Bumping version: {current} -> {new} ({bump_type})")
    update_files(current, new)
    print(f"\n✓ Version bumped to {new}")
    print(f"\nNext steps:")
    print(f"  1. git add src/tennis_elo/__init__.py pyproject.toml")
    print(f"  2. git commit -m 'Bump version to {new}'")
    print(f"  3. git tag v{new}")
    print(f"  4. git push --tags")

if __name__ == "__main__":
    main()
