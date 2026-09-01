#!/usr/bin/env python3
"""
download_gh_artifacts.py

Downloads GitHub Actions artifacts for a repo, either from a specific
workflow run or the latest run of a given workflow (optionally filtered
by branch).

Requirements: requests  (pip install requests --break-system-packages)

Auth: export a GitHub token with `repo` (or `actions:read`) scope:
    export GITHUB_TOKEN=ghp_xxxxxxxxxxxx

Usage:
    python download_gh_artifacts.py -r owner/repo -o ./artifacts [options]

Examples:
    python download_gh_artifacts.py -r acme/widgets -R 123456789
    python download_gh_artifacts.py -r acme/widgets -w ci.yml -b main
    python download_gh_artifacts.py -r acme/widgets -w ci.yml -b main -n "build-*"
"""

import argparse
import fnmatch
import os
import sys
import tarfile
import zipfile
from io import BytesIO

import requests

TAR_MODES = {
    ".tar": "r:",
    ".tar.gz": "r:gz",
    ".tgz": "r:gz",
    ".tar.bz2": "r:bz2",
    ".tar.xz": "r:xz",
}


def _tar_mode_for(filename: str) -> str | None:
    lower = filename.lower()
    for ext, mode in TAR_MODES.items():
        if lower.endswith(ext):
            return mode
    return None


def extract_nested_archives(directory: str):
    """Find zip/tar archives inside an extracted artifact and extract those too."""
    for entry in os.listdir(directory):
        path = os.path.join(directory, entry)
        if not os.path.isfile(path):
            continue

        tar_mode = _tar_mode_for(entry)
        if tar_mode:
            dest = os.path.join(directory, entry.split(".tar")[0] + "_tar")
            os.makedirs(dest, exist_ok=True)
            try:
                with tarfile.open(path, tar_mode) as tf:
                    tf.extractall(dest)
                print(f"    Extracted nested tarball '{entry}' -> {dest}")
            except tarfile.TarError as e:
                print(f"    Warning: failed to extract '{entry}': {e}")
        elif entry.lower().endswith(".zip"):
            dest = os.path.join(directory, entry[:-4] + "_zip")
            os.makedirs(dest, exist_ok=True)
            try:
                with zipfile.ZipFile(path) as zf:
                    zf.extractall(dest)
                print(f"    Extracted nested zip '{entry}' -> {dest}")
            except zipfile.BadZipFile as e:
                print(f"    Warning: failed to extract '{entry}': {e}")

API = "https://api.github.com"


def gh_session(token: str) -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    return s


def resolve_run_id(session: requests.Session, repo: str, workflow: str, branch: str | None) -> int:
    print(f"Looking up latest successful run for workflow '{workflow}'"
          + (f" on branch '{branch}'" if branch else "") + "...")
    params = {"per_page": 1, "status": "success"}
    if branch:
        params["branch"] = branch

    resp = session.get(f"{API}/repos/{repo}/actions/workflows/{workflow}/runs", params=params)
    resp.raise_for_status()
    runs = resp.json().get("workflow_runs", [])
    if not runs:
        print("Error: no matching workflow run found", file=sys.stderr)
        sys.exit(1)

    run_id = runs[0]["id"]
    print(f"Resolved run ID: {run_id}")
    return run_id


def resolve_latest_run_repo_wide(session: requests.Session, repo: str, branch: str | None) -> int:
    """Find the most recent successful run across ALL workflows in the repo."""
    print("Looking up latest successful run across all workflows"
          + (f" on branch '{branch}'" if branch else "") + "...")
    params = {"per_page": 1, "status": "success"}
    if branch:
        params["branch"] = branch

    resp = session.get(f"{API}/repos/{repo}/actions/runs", params=params)
    resp.raise_for_status()
    runs = resp.json().get("workflow_runs", [])
    if not runs:
        print("Error: no successful workflow runs found for this repo", file=sys.stderr)
        sys.exit(1)

    run_id = runs[0]["id"]
    print(f"Resolved run ID: {run_id} (workflow: {runs[0].get('name', 'unknown')})")
    return run_id


def download_artifacts(
    session: requests.Session,
    repo: str,
    run_id: int,
    out_dir: str,
    name_filter: str | None,
):
    print(f"Fetching artifact list for run {run_id}...")
    resp = session.get(
        f"{API}/repos/{repo}/actions/runs/{run_id}/artifacts", params={"per_page": 100}
    )
    resp.raise_for_status()
    artifacts = resp.json().get("artifacts", [])

    if not artifacts:
        print(f"No artifacts found for run {run_id}.")
        return

    print(f"Found {len(artifacts)} artifact(s).")
    os.makedirs(out_dir, exist_ok=True)

    for artifact in artifacts:
        name = artifact["name"]
        artifact_id = artifact["id"]
        expired = artifact["expired"]
        size = artifact["size_in_bytes"]

        if name_filter and not fnmatch.fnmatch(name, name_filter):
            print(f"Skipping '{name}' (doesn't match filter '{name_filter}')")
            continue

        if expired:
            print(f"Skipping '{name}' (expired, no longer downloadable)")
            continue

        print(f"Downloading '{name}' ({size} bytes)...")
        dl_resp = session.get(
            f"{API}/repos/{repo}/actions/artifacts/{artifact_id}/zip", stream=True
        )
        dl_resp.raise_for_status()

        zip_path = os.path.join(out_dir, f"{name}.zip")
        with open(zip_path, "wb") as f:
            for chunk in dl_resp.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"  Saved zip -> {zip_path}")

        extract_dir = os.path.join(out_dir, name)
        os.makedirs(extract_dir, exist_ok=True)
        try:
            with zipfile.ZipFile(zip_path) as zf:
                zf.extractall(extract_dir)
            print(f"  Extracted to {extract_dir}")
            extract_nested_archives(extract_dir)
        except zipfile.BadZipFile:
            print(f"  Warning: '{zip_path}' is not a valid zip, left as-is")

    print(f"Done. Artifacts saved under: {out_dir}")


def main():
    parser = argparse.ArgumentParser(description="Download GitHub Actions artifacts")
    parser.add_argument("-r", "--repo", required=True, help="owner/repo")
    parser.add_argument("-o", "--out-dir", default="./artifacts", help="output directory")
    parser.add_argument("-R", "--run-id", type=int, help="specific workflow run ID")
    parser.add_argument(
        "-w", "--workflow",
        help="workflow file or ID, e.g. ci.yml (optional - if omitted, uses the "
             "most recent successful run across ALL workflows in the repo)",
    )
    parser.add_argument("-b", "--branch", help="filter latest run by branch")
    parser.add_argument("-n", "--name-filter", help="glob filter for artifact names, e.g. 'build-*'")
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("Error: set GITHUB_TOKEN env var", file=sys.stderr)
        sys.exit(1)

    session = gh_session(token)

    run_id = args.run_id
    if not run_id:
        if args.workflow:
            run_id = resolve_run_id(session, args.repo, args.workflow, args.branch)
        else:
            run_id = resolve_latest_run_repo_wide(session, args.repo, args.branch)

    download_artifacts(session, args.repo, run_id, args.out_dir, args.name_filter)


if __name__ == "__main__":
    main()