"""API Sentinel - Release Candidate Packaging & Verification Script.

Creates a sanitized release candidate in dist/release_candidate_v1.1.0
and archives it into dist/API_Sentinel_v1.1.0_Release_Candidate.zip.
"""

import os
import shutil
import zipfile
from pathlib import Path

ROOT_DIR = Path(r"C:\PROJECTS\api-sentinel")
DIST_DIR = ROOT_DIR / "dist"
STAGING_DIR = DIST_DIR / "release_candidate_v1.1.0"
OUTPUT_ZIP = DIST_DIR / "API_Sentinel_v1.1.0_Release_Candidate.zip"

EXCLUDE_DIRS = {
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".git",
    ".venv",
    "venv",
    "env",
    "dist",  # Avoid recursive inclusion of dist/
}

EXCLUDE_FILE_PATTERNS = {
    ".env",
    ".env.local",
    "api_sentinel.db",
    "api_sentinel.db-wal",
    "api_sentinel.db-shm",
    "*.sqlite3",
    "*.pyc",
    "*.pyo",
    "*.pyd",
    "*.log",
    "*.zip",
    "*.bak",
}

def is_excluded(path: Path) -> bool:
    # Check directory components
    for part in path.parts:
        if part in EXCLUDE_DIRS:
            return True
    
    # Check file name
    name = path.name
    if name in (".env", ".env.local"):
        return True
    if name.endswith((".db", ".db-wal", ".db-shm", ".sqlite3", ".pyc", ".pyo", ".pyd", ".log", ".zip", ".bak")):
        return True
    if name == "test_cap.png":
        return True
    return False

def package_release():
    print("=" * 65)
    print("API SENTINEL — RELEASE CANDIDATE PACKAGING & SANITIZATION")
    print("=" * 65)
    
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    if STAGING_DIR.exists():
        print(f"Cleaning existing staging directory: {STAGING_DIR}")
        shutil.rmtree(STAGING_DIR)
    STAGING_DIR.mkdir(parents=True, exist_ok=True)
    
    # Top-level directories to copy
    source_dirs = ["backend", "frontend", "dashboard", "dataset", "demo_api", "docs", "metadata", "scripts"]
    
    total_copied = 0
    for sdir in source_dirs:
        src_path = ROOT_DIR / sdir
        if not src_path.exists():
            continue
        dest_path = STAGING_DIR / sdir
        print(f"Packaging {sdir}/...")
        for root, dirs, files in os.walk(src_path):
            # prune excluded dirs in-place
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not (Path(root) / d == DIST_DIR)]
            
            rel_dir = Path(root).relative_to(ROOT_DIR)
            target_dir = STAGING_DIR / rel_dir
            target_dir.mkdir(parents=True, exist_ok=True)
            
            for file in files:
                file_path = Path(root) / file
                if not is_excluded(file_path):
                    shutil.copy2(file_path, target_dir / file)
                    total_copied += 1
    
    # Copy essential root files
    root_files = [
        "Dockerfile",
        "docker-compose.yml",
        ".dockerignore",
        ".gitignore",
        ".env.example",
        "README.md",
        "start-development.ps1",
        "start-production.ps1",
        "stop-api-sentinel.ps1",
    ]
    for rf in root_files:
        src_file = ROOT_DIR / rf
        if src_file.exists():
            shutil.copy2(src_file, STAGING_DIR / rf)
            total_copied += 1
            print(f"Copied root file: {rf}")

    # Also ensure frontend production build dist is included in frontend/dist
    frontend_dist_src = ROOT_DIR / "frontend" / "dist"
    if frontend_dist_src.exists():
        frontend_dist_target = STAGING_DIR / "frontend" / "dist"
        print("Copying compiled frontend production dist...")
        shutil.copytree(frontend_dist_src, frontend_dist_target, dirs_exist_ok=True)

    print(f"\nStaging complete: {total_copied} sanitized files assembled.")
    
    # Create clean zip archive
    if OUTPUT_ZIP.exists():
        OUTPUT_ZIP.unlink()
        
    print(f"Compressing into: {OUTPUT_ZIP.name}...")
    with zipfile.ZipFile(OUTPUT_ZIP, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(STAGING_DIR):
            for file in files:
                file_path = Path(root) / file
                archive_name = file_path.relative_to(STAGING_DIR)
                zipf.write(file_path, archive_name)
                
    zip_size_mb = OUTPUT_ZIP.stat().st_size / (1024 * 1024)
    print(f"Release Candidate Archive Created Successfully! Size: {zip_size_mb:.2f} MB")
    
    # Audit Zip Archive for Prohibited Content
    print("\nAuditing Zip Archive for Prohibited Content & Secrets...")
    prohibited_found = []
    with zipfile.ZipFile(OUTPUT_ZIP, "r") as zipf:
        namelist = zipf.namelist()
        for name in namelist:
            p = Path(name)
            if p.name in (".env", ".env.local"):
                prohibited_found.append(name)
            if any(name.endswith(ext) for ext in [".db", ".db-wal", ".db-shm", ".sqlite3"]):
                prohibited_found.append(name)
            if "node_modules" in p.parts:
                prohibited_found.append(name)
            if "__pycache__" in p.parts:
                prohibited_found.append(name)
                
    if prohibited_found:
        print(f"ERROR: Prohibited files found in ZIP: {prohibited_found}")
        return False
    else:
        print("AUDIT PASS: Zero .env files, zero database files, zero node_modules, zero __pycache__.")
        print(f"Total files in clean release candidate archive: {len(namelist)}")
        return True

if __name__ == "__main__":
    success = package_release()
    exit(0 if success else 1)
