#!/usr/bin/env python3
"""
restore_svn.py — Restore SVN repositories from .bz2 dumps made by backup_svn.py.

For each archive, this creates a brand-new repo with `svnadmin create` and
pipes the decompressed dump into it with `svnadmin load`. It never touches
an existing repo directory — if the target already exists, that archive is
skipped (use --force to wipe and recreate it instead).

Two modes:

  1. Single archive, explicit target (safest, recommended for one-offs):
       python3 restore_svn.py --archive svn-maxikat-specview-backup-20260830_140000.bz2 \\
           --target /var/www/svn/maxikat/specview

  2. Bulk restore, a whole directory of archives:
       python3 restore_svn.py --src /var/backups/svn --dest-root /var/www/svn

     In bulk mode the target dir name is derived from the archive filename
     (the part between "svn-" and "-backup-"). By default that label is used
     as-is (flat), e.g. "maxikat-specview" -> <dest-root>/maxikat-specview.
     Pass --nested to turn dashes back into path separators instead, e.g.
     "maxikat-specview" -> <dest-root>/maxikat/specview. Only use --nested
     if you're sure none of your original repo names contained dashes
     themselves, since that makes the reverse mapping ambiguous.

Requires: svnadmin and bzip2 available on PATH. Python 3.6+.
"""

import argparse
import logging
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

log = logging.getLogger("restore_svn")

ARCHIVE_RE = re.compile(r"^svn-(.+)-backup-\d{8}_\d{6}\.bz2$")


def setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def _safe_rmtree(path: Path) -> None:
    try:
        shutil.rmtree(str(path))
    except FileNotFoundError:
        pass


def check_tools() -> bool:
    for tool in ("svnadmin", "bzip2"):
        if shutil.which(tool) is None:
            log.error("Required tool not found on PATH: %s", tool)
            return False
    return True


def label_to_target(label: str, dest_root: Path, nested: bool) -> Path:
    if nested:
        return dest_root.joinpath(*label.split("-"))
    return dest_root / label


def restore_one(archive: Path, target: Path, force: bool) -> bool:
    if target.exists():
        if not force:
            log.warning("Target already exists, skipping: %s (use --force to overwrite)", target)
            return False
        log.warning("Removing existing target due to --force: %s", target)
        _safe_rmtree(target)

    target.parent.mkdir(parents=True, exist_ok=True)

    log.info("Creating repo at %s", target)
    try:
        subprocess.run(
            ["svnadmin", "create", str(target)],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        log.error("svnadmin create failed for %s: %s", target, e.stderr.strip())
        return False

    log.info("Loading dump %s -> %s", archive.name, target)
    try:
        with open(str(archive), "rb") as in_f:
            bzip = subprocess.Popen(
                ["bzip2", "-dc"],
                stdin=in_f,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            load = subprocess.Popen(
                ["svnadmin", "load", "-q", str(target)],
                stdin=bzip.stdout,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            bzip.stdout.close()
            _, load_err = load.communicate()
            _, bzip_err = bzip.communicate()
    except FileNotFoundError as e:
        log.error("Command not found (%s).", e)
        _safe_rmtree(target)
        return False

    if bzip.returncode != 0:
        log.error("bzip2 decompression failed for %s: %s", archive.name, bzip_err.decode().strip())
        _safe_rmtree(target)
        return False
    if load.returncode != 0:
        log.error("svnadmin load failed for %s: %s", archive.name, load_err.decode().strip())
        _safe_rmtree(target)
        return False

    log.info("Restored: %s", target)
    return True


def discover_archives(src: Path, only: Optional[List[str]]) -> List[Path]:
    archives = []
    for f in sorted(src.glob("*.bz2")):
        m = ARCHIVE_RE.match(f.name)
        if not m:
            log.debug("Skipping %s (doesn't match expected naming pattern)", f.name)
            continue
        label = m.group(1)
        if only and label not in only:
            continue
        archives.append(f)
    return archives


def main() -> int:
    parser = argparse.ArgumentParser(description="Restore SVN repos from backup_svn.py .bz2 dumps.")

    single = parser.add_argument_group("single archive mode")
    single.add_argument("--archive", type=Path, help="Path to one .bz2 dump file")
    single.add_argument("--target", type=Path, help="Exact path to create the restored repo at")

    bulk = parser.add_argument_group("bulk mode")
    bulk.add_argument("--src", type=Path, help="Directory containing .bz2 dump files")
    bulk.add_argument("--dest-root", type=Path, help="Root directory to recreate repos under")
    bulk.add_argument("--nested", action="store_true", help="Turn dashes in archive labels back into nested paths")
    bulk.add_argument("--repos", type=str, default=None, help="Comma-separated list of labels to restore (default: all)")

    parser.add_argument("--force", action="store_true", help="Overwrite target(s) if they already exist")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose/debug logging")
    args = parser.parse_args()

    setup_logging(args.verbose)

    if not check_tools():
        return 1

    # Single-archive mode
    if args.archive:
        if not args.target:
            log.error("--target is required when using --archive")
            return 1
        if not args.archive.is_file():
            log.error("Archive not found: %s", args.archive)
            return 1
        ok = restore_one(args.archive, args.target, args.force)
        return 0 if ok else 1

    # Bulk mode
    if args.src:
        if not args.dest_root:
            log.error("--dest-root is required when using --src")
            return 1
        if not args.src.is_dir():
            log.error("Source directory does not exist: %s", args.src)
            return 1

        only = args.repos.split(",") if args.repos else None
        archives = discover_archives(args.src, only)
        if not archives:
            log.warning("No matching .bz2 archives found in %s", args.src)
            return 0

        log.info("Found %d archive(s) to restore", len(archives))
        failures = []
        for archive in archives:
            m = ARCHIVE_RE.match(archive.name)
            label = m.group(1)
            target = label_to_target(label, args.dest_root, args.nested)
            if not restore_one(archive, target, args.force):
                failures.append(archive.name)

        if failures:
            log.error("Restore finished with failures: %s", ", ".join(failures))
            return 1

        log.info("All repos restored successfully.")
        return 0

    parser.error("Provide either --archive/--target (single) or --src/--dest-root (bulk)")
    return 1  # unreachable, keeps type checkers happy


if __name__ == "__main__":
    sys.exit(main())