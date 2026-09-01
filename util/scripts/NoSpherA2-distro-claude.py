#!/usr/bin/env python3
"""
repackage_artifacts.py

Repackages downloaded/extracted GitHub Actions artifacts into distribution
zips, merging in extra external directories.

Expected layout (defaults, all overridable via CLI flags):

    artifacts/
        NoSpherA2-windows-x64/NoSpherA2-windows-x64_zip/   <- platform build
        NoSpherA2-macos-universal/NoSpherA2-macos-universal_tar/
        NoSpherA2-linux-x86_64/NoSpherA2-linux-x86_64_tar/
    hart-win64/         <- sibling of artifacts/, extra files for windows
    hart-mac64/         <- sibling of artifacts/, extra files for macos
    hart-lin64/         <- sibling of artifacts/, extra files for linux
    basis_sets/         <- sibling of artifacts/

Each output zip is built by flattening these into the zip root:
    - the platform build directory
    - the matching extra hart-XX directory
and adding the basis_sets directory as a "basis_sets/" folder.

Any file named NoSpherA2_Tests (with or without an extension, e.g.
NoSpherA2_Tests.exe) found in the platform build or extras directory is
skipped by default - pass --include-tests to keep them.

Resulting zip structure:
    basis_sets/...
    <platform build files>   (NoSpherA2_Tests[.exe] excluded by default)
    <hart-XX extra files>

Usage:
    python repackage_artifacts.py
    python repackage_artifacts.py --include-tests
    python repackage_artifacts.py --artifacts-dir ./artifacts --extras-dir . --out-dir ./dist
"""

import argparse
import os
import sys
import zipfile

# name -> (platform build dir relative to artifacts-dir, extra dir name relative to extras-dir)
PLATFORMS = {
    "hart-win64.zip": (
        os.path.join("NoSpherA2-windows-x64", "NoSpherA2-windows-x64_zip"),
        "hart-win64",
    ),
    "hart-mac64.zip": (
        os.path.join("NoSpherA2-macos-universal", "NoSpherA2-macos-universal_tar"),
        "hart-mac64",
    ),
    "hart-lin64.zip": (
        os.path.join("NoSpherA2-linux-x86_64", "NoSpherA2-linux-x86_64_tar"),
        "hart-lin64",
    ),
}


TEST_FILE_STEM = "nospherA2_tests".lower()


def _is_test_file(filename: str) -> bool:
    stem = os.path.splitext(filename)[0]
    return stem.lower() == TEST_FILE_STEM


def add_dir_to_zip(zf: zipfile.ZipFile, src_dir: str, arc_prefix: str = "", skip_tests: bool = False) -> int:
    """Add every file under src_dir into zf. Returns number of files added."""
    count = 0
    for root, _dirs, files in os.walk(src_dir):
        for fname in files:
            if skip_tests and _is_test_file(fname):
                continue
            full_path = os.path.join(root, fname)
            rel_path = os.path.relpath(full_path, src_dir)
            arcname = os.path.join(arc_prefix, rel_path) if arc_prefix else rel_path
            zf.write(full_path, arcname)
            count += 1
    return count


def build_zip(
    out_path: str,
    basis_sets_dir: str,
    platform_dir: str,
    extra_dir: str,
    include_tests: bool,
):
    print(f"Building {out_path} ...")
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
        if os.path.isdir(basis_sets_dir):
            n = add_dir_to_zip(zf, basis_sets_dir, arc_prefix="basis_sets")
            print(f"  + basis_sets/  ({n} files from {basis_sets_dir})")
        else:
            print(f"  Warning: basis_sets dir not found: {basis_sets_dir}", file=sys.stderr)

        if os.path.isdir(platform_dir):
            n = add_dir_to_zip(zf, platform_dir, skip_tests=not include_tests)
            print(f"  + platform build  ({n} files from {platform_dir})")
        else:
            print(f"  Warning: platform build dir not found: {platform_dir}", file=sys.stderr)

        if os.path.isdir(extra_dir):
            n = add_dir_to_zip(zf, extra_dir, skip_tests=not include_tests)
            print(f"  + extras  ({n} files from {extra_dir})")
        else:
            print(f"  Warning: extras dir not found: {extra_dir}", file=sys.stderr)

    print(f"Done: {out_path}")


def main():
    parser = argparse.ArgumentParser(description="Repackage artifacts into distribution zips")
    parser.add_argument("--artifacts-dir", default="./artifacts", help="downloaded/extracted artifacts directory")
    parser.add_argument("--extras-dir", default=None,
                         help="directory containing hart-winXX/hart-macXX/hart-linXX and basis_set "
                              "(default: parent directory of --artifacts-dir)")
    parser.add_argument("--include-tests", action="store_true",
                         help="keep NoSpherA2_Tests / NoSpherA2_Tests.exe files (skipped by default)")
    parser.add_argument("--out-dir", default="./dist", help="output directory for the distribution zips")
    args = parser.parse_args()

    artifacts_dir = os.path.abspath(args.artifacts_dir)
    extras_dir = os.path.abspath(args.extras_dir) if args.extras_dir else os.path.dirname(artifacts_dir)
    out_dir = os.path.abspath(args.out_dir)
    os.makedirs(out_dir, exist_ok=True)

    basis_sets_dir = os.path.join(extras_dir, "basis_sets")

    for zip_name, (platform_rel, extra_name) in PLATFORMS.items():
        platform_dir = os.path.join(artifacts_dir, platform_rel)
        extra_dir = os.path.join(extras_dir, extra_name)
        out_path = os.path.join(out_dir, zip_name)
        build_zip(out_path, basis_sets_dir, platform_dir, extra_dir, args.include_tests)

    print(f"\nAll done. Distribution zips are in: {out_dir}")


if __name__ == "__main__":
    main()