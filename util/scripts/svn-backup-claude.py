#!/usr/bin/env python3
"""
backup_svn.py — Back up every SVN repository found under a directory tree.

Recursively searches --src for SVN repo dirs (identified by a "format"
file + "db" subdir — repos can be nested, e.g. /var/www/svn/maxikat/specview/).
For each repo found, runs the equivalent of:

    svnadmin dump -q <repo> | bzip2 -9 > svn-<path>-backup-<timestamp>.bz2

...and writes the result into --dest. Optionally deletes backups older
than --keep-days.

Usage:
    python3 backup_svn.py --src /var/www/svn --dest /var/backups/svn
    python3 backup_svn.py --src /var/www/svn --dest /var/backups/svn --keep-days 14
    python3 backup_svn.py --src /var/www/svn --dest /var/backups/svn --repos maxikat/specview

Requires: svnadmin and bzip2 available on PATH.
"""

import argparse
import logging
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Set

log = logging.getLogger("backup_svn")


def setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def is_svn_repo(path: Path) -> bool:
    """A real SVN repo dir has a 'format' file and a 'db' subdir."""
    return (path / "format").is_file() and (path / "db").is_dir()


def _safe_unlink(path: Path) -> None:
    """Path.unlink(missing_ok=True) needs Python 3.8+; this works on 3.6."""
    try:
        path.unlink()
    except FileNotFoundError:
        pass


def discover_repos(src: Path, only: Optional[Set[str]]) -> List[Path]:
    """
    Recursively find SVN repo dirs under src (repos can be nested, e.g.
    /var/www/svn/maxikat/specview/). Stops descending once a repo dir is
    found, since a repo's own internals (db/, conf/, etc.) are never
    themselves repos.
    """
    repos = []

    def _walk(path: Path):
        for entry in sorted(path.iterdir()):
            if not entry.is_dir():
                continue
            if is_svn_repo(entry):
                label = str(entry.relative_to(src))
                if only and label not in only and entry.name not in only:
                    log.debug("Skipping %s (not in --repos filter)", label)
                    continue
                repos.append(entry)
            else:
                _walk(entry)

    _walk(src)
    return repos


def backup_repo(repo: Path, src: Path, dest: Path, timestamp: str) -> bool:
    """
    svnadmin dump -q <repo> | bzip2 -9 > dest/svn-<path>-backup-<timestamp>.bz2
    Mirrors: svnadmin dump -q /var/www/svn/maxikat/specview/ | bzip2 -9 > ...
    """
    rel_label = str(repo.relative_to(src)).replace("/", "-")
    archive_name = f"svn-{rel_label}-backup-{timestamp}.bz2"
    archive_path = dest / archive_name

    log.info("Dumping %s -> %s", repo.relative_to(src), archive_name)
    try:
        with open(archive_path, "wb") as out_f:
            dump = subprocess.Popen(
                ["svnadmin", "dump", "-q", str(repo)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            bzip = subprocess.Popen(
                ["bzip2", "-9"],
                stdin=dump.stdout,
                stdout=out_f,
                stderr=subprocess.PIPE,
            )
            dump.stdout.close()  # allow dump to receive SIGPIPE if bzip exits
            _, bzip_err = bzip.communicate()
            _, dump_err = dump.communicate()
    except FileNotFoundError as e:
        log.error("Command not found (%s). Is subversion/bzip2 installed?", e)
        _safe_unlink(archive_path)
        return False

    if dump.returncode != 0:
        log.error("svnadmin dump failed for %s: %s", repo.name, dump_err.decode().strip())
        _safe_unlink(archive_path)
        return False
    if bzip.returncode != 0:
        log.error("bzip2 failed for %s: %s", repo.name, bzip_err.decode().strip())
        _safe_unlink(archive_path)
        return False

    size_mb = archive_path.stat().st_size / (1024 * 1024)
    log.info("Done: %s (%.1f MB)", archive_name, size_mb)
    return True


def cleanup_old_backups(dest: Path, keep_days: int) -> None:
    if keep_days <= 0:
        return
    cutoff = datetime.now() - timedelta(days=keep_days)
    for f in dest.glob("*.bz2"):
        if datetime.fromtimestamp(f.stat().st_mtime) < cutoff:
            log.info("Removing old backup: %s", f.name)
            f.unlink()


def main() -> int:
    parser = argparse.ArgumentParser(description="Back up all SVN repos in a directory.")
    parser.add_argument("--src", required=True, type=Path, help="Directory containing SVN repos, e.g. /var/www/svn")
    parser.add_argument("--dest", required=True, type=Path, help="Directory to write backup archives to")
    parser.add_argument("--repos", type=str, default=None, help="Comma-separated list of repo names to back up (default: all)")
    parser.add_argument("--keep-days", type=int, default=0, help="Delete backups older than N days (default: 0 = never delete)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose/debug logging")
    args = parser.parse_args()

    setup_logging(args.verbose)

    if not args.src.is_dir():
        log.error("Source directory does not exist: %s", args.src)
        return 1

    args.dest.mkdir(parents=True, exist_ok=True)

    only = set(args.repos.split(",")) if args.repos else None
    repos = discover_repos(args.src, only)

    if not repos:
        log.warning("No SVN repos found in %s", args.src)
        return 0

    log.info("Found %d repo(s): %s", len(repos), ", ".join(str(r.relative_to(args.src)) for r in repos))

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    failures = []
    for repo in repos:
        if not backup_repo(repo, args.src, args.dest, timestamp):
            failures.append(str(repo.relative_to(args.src)))

    cleanup_old_backups(args.dest, args.keep_days)

    if failures:
        log.error("Backup finished with failures: %s", ", ".join(failures))
        return 1

    log.info("All repos backed up successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())