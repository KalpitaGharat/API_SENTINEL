"""API Sentinel - Complete Project Packaging Script for Distribution & Sharing.

Packages the entire project into a clean, sanitized zip archive:
- Preserves all source code: backend, frontend, dashboard, demo_api, dataset, docs, metadata, scripts.
- Preserves compiled frontend production build (frontend/dist).
- Preserves startup scripts (start-development.ps1, start-production.ps1, stop-api-sentinel.ps1), Dockerfile, README.
- Excludes bloat and sensitive files: node_modules, .git, __pycache__, .venv, .env secrets, and database files.
- Generates C:\\PROJECTS\\API_Sentinel_Complete_Project.zip.
"""

import os
import shutil
import zipfile
from pathlib import Path

ROOT_DIR = Path(r"C:\PROJECTS\api-sentinel")
DIST_DIR = ROOT_DIR / "dist"
STAGING_DIR = DIST_DIR / "project_export_staging"
OUTPUT_ZIP_DIST = DIST_DIR / "API_Sentinel_Complete_Project.zip"
OUTPUT_ZIP_PROJECTS = Path(r"C:\PROJECTS\API_Sentinel_Complete_Project.zip")

EXCLUDE_DIRS = {
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".git",
    ".venv",
    "venv",
    "env",
    "dist",
    "project_export_staging",
    "release_candidate_v1.1.0",
}

def is_excluded(path: Path) -> bool:
    for part in path.parts:
        if part in EXCLUDE_DIRS:
            return True
    
    name = path.name
    # Keep .env and .env.example since user explicitly requested including .env
    # Only exclude other temporary local files
    if name in (".env.local",):
        return True
    # Exclude runtime database files and binary caches
    if name.endswith((".db", ".db-wal", ".db-shm", ".sqlite3", ".pyc", ".pyo", ".pyd", ".log", ".bak")):
        return True
    # Do not re-zip zip files inside the tree
    if name.endswith(".zip"):
        return True
    return False

def package_project():
    print("=" * 70)
    print("API SENTINEL — PACKAGING PROJECT FOR SHARING & DISTRIBUTION")
    print("=" * 70)

    DIST_DIR.mkdir(parents=True, exist_ok=True)
    if STAGING_DIR.exists():
        print(f"Cleaning existing staging directory: {STAGING_DIR}")
        shutil.rmtree(STAGING_DIR)
    STAGING_DIR.mkdir(parents=True, exist_ok=True)

    # Directories to package
    target_dirs = [
        "backend",
        "frontend",
        "dashboard",
        "dataset",
        "demo_api",
        "docs",
        "metadata",
        "scripts",
    ]

    total_copied = 0
    for folder in target_dirs:
        src_path = ROOT_DIR / folder
        if not src_path.exists():
            continue
        print(f"Adding {folder}/...")
        for root, dirs, files in os.walk(src_path):
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not (Path(root) / d == DIST_DIR)]
            rel_dir = Path(root).relative_to(ROOT_DIR)
            target_sub = STAGING_DIR / rel_dir
            target_sub.mkdir(parents=True, exist_ok=True)
            for f in files:
                f_path = Path(root) / f
                if not is_excluded(f_path):
                    shutil.copy2(f_path, target_sub / f)
                    total_copied += 1

    # Copy root files
    root_files = [
        "Dockerfile",
        "docker-compose.yml",
        ".dockerignore",
        ".gitignore",
        ".env",
        ".env.example",
        "README.md",
        "start-development.ps1",
        "start-production.ps1",
        "stop-api-sentinel.ps1",
    ]
    for rf in root_files:
        src = ROOT_DIR / rf
        if src.exists():
            shutil.copy2(src, STAGING_DIR / rf)
            total_copied += 1
            print(f"Adding root configuration: {rf}")

    # If root .env did not exist, copy backend/.env to staging root .env as well
    if not (STAGING_DIR / ".env").exists() and (ROOT_DIR / "backend" / ".env").exists():
        shutil.copy2(ROOT_DIR / "backend" / ".env", STAGING_DIR / ".env")
        total_copied += 1
        print("Provisioned root .env from backend/.env for plug-and-play setup")

    # Ensure frontend production dist is bundled
    frontend_dist_src = ROOT_DIR / "frontend" / "dist"
    if frontend_dist_src.exists():
        print("Including compiled frontend distribution (frontend/dist)...")
        shutil.copytree(frontend_dist_src, STAGING_DIR / "frontend" / "dist", dirs_exist_ok=True)

    print(f"\nStaging complete: {total_copied} clean files prepared.")

    # Compress into distribution zip
    print(f"\nCompressing files into archive...")
    if OUTPUT_ZIP_DIST.exists():
        OUTPUT_ZIP_DIST.unlink()

    with zipfile.ZipFile(OUTPUT_ZIP_DIST, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(STAGING_DIR):
            for file in files:
                fpath = Path(root) / file
                arcname = fpath.relative_to(STAGING_DIR)
                # Archive with api-sentinel root prefix for clean extraction
                zipf.write(fpath, Path("api-sentinel") / arcname)

    # Copy to C:\PROJECTS\API_Sentinel_Complete_Project.zip for easy access
    shutil.copy2(OUTPUT_ZIP_DIST, OUTPUT_ZIP_PROJECTS)

    zip_size_mb = OUTPUT_ZIP_PROJECTS.stat().st_size / (1024 * 1024)
    print(f"\nSUCCESS! ZIP Archive generated at:")
    print(f"  1. {OUTPUT_ZIP_PROJECTS} ({zip_size_mb:.2f} MB)")
    print(f"  2. {OUTPUT_ZIP_DIST} ({zip_size_mb:.2f} MB)")

    # Audit archive
    print("\nAuditing Archive Contents:")
    with zipfile.ZipFile(OUTPUT_ZIP_PROJECTS, "r") as z:
        names = z.namelist()
        has_env = any(Path(n).name in (".env", ".env.local") for n in names)
        has_node_modules = any("node_modules" in Path(n).parts for n in names)
        has_pycache = any("__pycache__" in Path(n).parts for n in names)
        has_git = any(".git" in Path(n).parts for n in names)
        has_db = any(n.endswith((".db", ".sqlite3")) for n in names)

        print(f"  • Total files archived: {len(names)}")
        print(f"  • Node modules excluded: {'YES' if not has_node_modules else 'NO'}")
        print(f"  • .git directory excluded: {'YES' if not has_git else 'NO'}")
        print(f"  • .env configuration included: {'YES' if has_env else 'NO'}")
        print(f"  • SQLite databases excluded: {'YES' if not has_db else 'NO'}")
        print(f"  • Python caches excluded: {'YES' if not has_pycache else 'NO'}")

    # Cleanup staging directory
    shutil.rmtree(STAGING_DIR)
    print("\nTemporary staging directory cleaned up.")
    return True

if __name__ == "__main__":
    package_project()
