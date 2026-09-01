#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
log_reader.py -- OLEX2 usage-log analyzer.

Parses server log files to report on:
  - Successful installations (unique + total, by date)
  - "Startup" events (a client hitting index.ind with HEAD), by date
  - Unique IPs and unique client tokens ("at ...")
  - Long-term users (distinct-day counts per IP)
  - Branch / platform / branch+platform usage breakdowns

This is a refactor of an earlier script. The parsing rules (what counts as
an "installation", a "startup", etc.) are preserved exactly from the
original so results stay comparable -- see the NOTE comments below for the
handful of assumptions baked into the original format that could use
verification against real log samples.

Usage:
    python3 log_reader.py --dir ./test/ --pattern '.log'
    python3 log_reader.py --dir ./test/ --json report.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

IP_PATTERN = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")

# A session id is expected to sit inside parentheses and be exactly 32
# characters long, e.g. an MD5 hex digest: "Handling ... (32chars) at ..."
SESSION_ID_LENGTH = 32


@dataclass
class LogEvent:
    """A single parsed line of interest, with the fields callers need."""

    ip: str
    full_date: str  # e.g. "2020-01-05T10:00:00"
    month: str  # full_date[:7], e.g. "2020-01"
    token: Optional[str] = None  # the "(at TOKEN)" value, if present


@dataclass
class Stats:
    """All aggregated counters, gathered across every log file processed."""

    unique_ips: set = field(default_factory=set)
    unique_tokens: set = field(default_factory=set)
    unique_ip_branch: set = field(default_factory=set)

    # Installations
    installations_raw_total: int = 0  # every matching GET, including same-day retries/resumes
    installations_total: int = 0  # collapsed: one per (person, day) -- see install_sessions_seen
    install_sessions_seen: set = field(
        default_factory=set
    )  # {(dedup_key, full_date)} -- collapses same-day repeat/resume downloads into one event
    installs_by_ip: Counter = field(
        default_factory=Counter
    )  # ip -> raw install count (all installs, incl. dupes)
    installs_by_date: Counter = field(default_factory=Counter)  # collapsed session count, by month
    installs_unique_by_date: Counter = field(
        default_factory=Counter
    )  # first-time-ever-per-key installs
    # (at=...) is present only when the user consented to tracking, so it's
    # split explicitly rather than blended into one dedup key: token-based
    # counts are a reliable unique-user count for the consenting cohort;
    # IP-based counts are a rough proxy for everyone else and can both
    # over-count (shared/NAT IPs) and under-count (rotating IPs).
    installs_tracked_tokens: Counter = field(
        default_factory=Counter
    )  # token -> count, consenting users only
    installs_untracked_ips: Counter = field(
        default_factory=Counter
    )  # ip -> count, declined/no token only

    # Startups (index.ind HEAD hits)
    # counts events per (ip, full_date) so repeats within the same
    # timestamp bucket collapse to one
    startups_seen: set = field(default_factory=set)  # {(ip, full_date)}
    startups_by_date: Counter = field(default_factory=Counter)  # first-seen-per-ip-per-day
    # Distinct-day tracking, split the same way as installs above: token
    # preferred (reliable, consenting users), IP as fallback (rough proxy).
    active_dates_by_token: dict = field(
        default_factory=lambda: defaultdict(set)
    )  # token -> {full_date,...}
    active_dates_by_ip_untracked: dict = field(
        default_factory=lambda: defaultdict(set)
    )  # ip -> {full_date,...}, no-token events only

    startups_by_token_date: set = field(default_factory=set)  # {(token, full_date)}
    startups_by_token_month: Counter = field(default_factory=Counter)

    # First date each token was ever seen
    token_first_date: dict = field(default_factory=dict)
    token_first_date_counts: Counter = field(
        default_factory=Counter
    )  # month -> count of tokens first seen then
    # Day-granularity first-seen tracking, used to split installs into
    # "new" (token's first-ever-seen day) vs. "returning" (token was
    # already active on an earlier day -- likely a build/update re-fetch,
    # not a fresh install). Token-only: IP is too unstable across days to
    # support this distinction for the untracked/declined-tracking cohort.
    token_first_seen_day: dict = field(default_factory=dict)  # token -> earliest full_date seen
    installs_new_by_date: Counter = field(
        default_factory=Counter
    )  # month -> count, token's first-ever day
    installs_returning_by_date: Counter = field(
        default_factory=Counter
    )  # month -> count, token seen on an earlier day too

    # Branch / platform usage
    branches: Counter = field(default_factory=Counter)
    platforms: Counter = field(default_factory=Counter)
    platform_branch: Counter = field(default_factory=Counter)
    install_platforms: Counter = field(default_factory=Counter)


def parse_common_fields(tokens: list[str]) -> tuple[str, str, Optional[str]]:
    """
    Given whitespace-split tokens of a log line, extract (full_date, month, token).
    full_date/month are '' if no "at <date>" field is present.
    """
    full_date = ""
    month = ""
    at_token = None
    for j, tok in enumerate(tokens):
        if tok == "at" and j + 1 < len(tokens):
            full_date = tokens[j + 1]
            month = full_date[:7]
        elif tok.startswith("(at") and tok.endswith(")"):
            at_token = tok[1:-1]
    return full_date, month, at_token


def extract_ip(tokens: list[str]) -> Optional[str]:
    """
    tokens[1] should be an IP address. The original format sometimes splits
    an IPv6-ish or comma-containing address across tokens[1] and tokens[2]
    (e.g. "1.2.3.4," "5.6.7.8" for an X-Forwarded-For style value) -- we
    preserve that by re-joining when tokens[1] ends in a comma.
    """
    if len(tokens) < 2:
        return None
    candidate = tokens[1]
    if IP_PATTERN.match(candidate):
        return candidate
    if "," in candidate and len(tokens) > 2:
        return candidate + tokens[2]
    return None


def extract_branch(line: str) -> Optional[str]:
    """
    Branch is the path segment between the first and second '/' after
    collapsing '//' to '/'. e.g. ".../1.2.3//index.ind" -> "1.2.3".
    """
    normalized = line.replace("//", "/")
    try:
        start = normalized.index("/")
        end = normalized.index("/", start + 1)
    except ValueError:
        return None
    branch = normalized[start + 1 : end]
    if " " in branch:
        branch = branch.split()[0]
    return branch


def is_startup_line(line: str) -> bool:
    return "index.ind" in line and "HEAD" in line


INSTALLER_FILE_PATTERN = re.compile(r"/olex2-[A-Za-z0-9._-]*\.(?:zip|exe|dmg)\b", re.IGNORECASE)


def is_installation_candidate(line: str) -> bool:
    """
    Redefined against real-world log evidence (see conversation notes):
    a genuine installation event is a GET request for a top-level
    'olex2-<platform>.(zip|exe|dmg)' file that carries an ' on <PLATFORM>'
    suffix. That suffix is stamped by the actual Olex2 client/updater
    (present on 99.8% of confirmed-genuine index.ind update checks) and is
    absent from scripted/bot traffic that bulk-downloads every platform
    variant back-to-back. Underscore-named accessory bundles (e.g.
    'olex2_fonts.zip', 'olex2_exe_sse.zip') are component fetches, not
    top-level installs, and are excluded by the hyphen-only filename
    pattern. HEAD requests are excluded (no genuine 'on'-tagged HEAD for
    an installer file was observed in the sample data).
    """
    if not line.startswith("Handling"):
        return False
    if " on " not in line:
        return False
    if not INSTALLER_FILE_PATTERN.search(line):
        return False
    method_match = re.search(r": (GET|HEAD) ", line)
    return bool(method_match and method_match.group(1) == "GET")


def extract_session_id(line: str) -> Optional[str]:
    """Session id is the (exactly 32-char) contents of the first '(...)' group."""
    open_idx = line.find("(")
    if open_idx == -1:
        return None
    close_idx = line.find(")", open_idx + 1)
    if close_idx == -1:
        return None
    if close_idx - open_idx - 1 != SESSION_ID_LENGTH:
        return None
    return line[open_idx : close_idx + 1]


def process_file(path: Path, stats: Stats) -> tuple[int, int]:
    """
    Parse a single log file, updating `stats` in place.
    Returns (successful_installations_in_file, unique_ips_installed_in_file).
    """
    lines = path.read_text(errors="replace").splitlines(keepends=True)
    lc = len(lines)

    file_install_ips: Counter = Counter()

    for i in range(lc):
        line = lines[i]
        tokens = line.split()
        if len(tokens) < 2:
            continue

        ip = extract_ip(tokens)
        if ip is None:
            continue

        full_date, month, token = parse_common_fields(tokens)

        if token:
            stats.unique_tokens.add(token)
            prev = stats.token_first_date.get(token)
            if prev is None or prev > month:
                stats.token_first_date[token] = month
            prev_day = stats.token_first_seen_day.get(token)
            if prev_day is None or prev_day > full_date:
                stats.token_first_seen_day[token] = full_date

        stats.unique_ips.add(ip)

        # --- Startup / branch / platform tracking ---
        if is_startup_line(line):
            branch = extract_branch(line)
            if branch and branch.startswith("1."):
                ip_branch_key = ip + branch
                if ip_branch_key not in stats.unique_ip_branch and " on " in line:
                    stats.unique_ip_branch.add(ip_branch_key)
                    stats.branches[branch] += 1
                    platform = line[line.index(" on ") + 4 :].strip()
                    stats.platforms[platform] += 1
                    stats.platform_branch[f"{platform} {branch}"] += 1

            event_key = (ip, full_date)
            if event_key not in stats.startups_seen:
                stats.startups_seen.add(event_key)
                stats.startups_by_date[month] += 1
                if token:
                    stats.active_dates_by_token[token].add(full_date)
                else:
                    stats.active_dates_by_ip_untracked[ip].add(full_date)

            if token:
                token_key = (token, full_date)
                if token_key not in stats.startups_by_token_date:
                    stats.startups_by_token_date.add(token_key)
                    stats.startups_by_token_month[month] += 1

        # --- Installation tracking ---
        if not is_installation_candidate(line):
            continue

        platform = line[line.rindex(" on ") + 4 :].strip()
        stats.install_platforms[platform] += 1

        stats.installations_raw_total += 1
        file_install_ips[ip] += 1
        stats.installs_by_ip[ip] += 1

        dedup_key = token if token else f"ip:{ip}"

        if token:
            stats.installs_tracked_tokens[token] += 1
            first_time_ever = stats.installs_tracked_tokens[token] == 1
        else:
            stats.installs_untracked_ips[ip] += 1
            first_time_ever = stats.installs_untracked_ips[ip] == 1
        if first_time_ever:
            stats.installs_unique_by_date[month] += 1

        # Collapse same-day repeat downloads (broken-download retries/resumes
        # by the same person) into a single install event. A download by the
        # same person on a *different* day still counts separately.
        session_key = (dedup_key, full_date)
        if session_key not in stats.install_sessions_seen:
            stats.install_sessions_seen.add(session_key)
            stats.installs_by_date[month] += 1
            stats.installations_total += 1

            if token:
                if stats.token_first_seen_day.get(token) == full_date:
                    stats.installs_new_by_date[month] += 1
                else:
                    stats.installs_returning_by_date[month] += 1

    return sum(file_install_ips.values()), len(file_install_ips)


def gather_log_files(directory: Path, pattern: str) -> list[Path]:
    files = sorted(p for p in directory.iterdir() if p.is_file() and pattern in p.name)
    return files


def print_report(stats: Stats) -> None:
    def date_line(d: str, c: int) -> None:
        print("%s-00 \t %d" % (d.replace(".", "-"), c))

    print("Total number of successful installations: %d" % stats.installations_total)
    if stats.installations_raw_total != stats.installations_total:
        print(
            "  (%d raw download requests before collapsing same-day retries/resumes)"
            % stats.installations_raw_total
        )
    print(
        "Total unique installations: %d tracked (consented, token-based) "
        "+ %d untracked (declined, IP-based proxy)"
        % (len(stats.installs_tracked_tokens), len(stats.installs_untracked_ips))
    )

    print("\nAll date stats")
    for d, c in stats.installs_by_date.items():
        date_line(d, c)

    print("\nUnique date installations")
    for d, c in stats.installs_unique_by_date.items():
        date_line(d, c)

    print("\nInstalls by new vs. returning token (tracked/consenting users only):")
    print("(returning = token was already active on an earlier day -- likely")
    print(" a build/update re-fetch rather than a fresh install)")
    for d, c in stats.installs_new_by_date.items():
        print("  new     %s-00 \t %d" % (d.replace(".", "-"), c))
    for d, c in stats.installs_returning_by_date.items():
        print("  return  %s-00 \t %d" % (d.replace(".", "-"), c))

    print("\nNumber of startups (max once per IP per day): %d" % len(stats.startups_seen))
    print("Unique date startups")
    for d, c in stats.startups_by_date.items():
        date_line(d, c)

    print("\nNumber of unique IPs: %d" % len(stats.unique_ips))

    print("\nLong-term usage (distinct active days), tracked users only, in buckets of 5:")
    print("(IP-based fallback for users who declined tracking is excluded here --")
    print(" IP can rotate day to day, so it isn't a reliable 'same person' signal.)")
    bucket_counts = [0] * 100
    bucket_tokens: list[Optional[set]] = [None] * 100
    for token, dates in stats.active_dates_by_token.items():
        n_days = len(dates)
        for x in range(len(bucket_counts)):
            if n_days >= (x + 1) * 5:
                bucket_counts[x] += 1
                if bucket_tokens[x] is None:
                    bucket_tokens[x] = set()
                bucket_tokens[x].add(token)
            else:
                break
    for x in range(len(bucket_counts)):
        threshold = (x + 1) * 5
        print(
            "Number of people who used Olex2 for at least %d days: %d"
            % (threshold, bucket_counts[x])
        )
        if bucket_counts[x] == 0:
            break

    for token, first_month in stats.token_first_date.items():
        stats.token_first_date_counts[first_month] += 1

    print("\nTotal number of unique tokens (consenting users only): %d" % len(stats.unique_tokens))
    for d, c in stats.token_first_date_counts.items():
        print("%s\t %d" % (d.replace(".", "-") + "-00", c))

    print("\nTotal number of unique token-startups: %d" % len(stats.startups_by_token_date))
    for d, c in stats.startups_by_token_month.items():
        print("%s\t %d" % (d.replace(".", "-") + "-00", c))

    print("\nBranch usage:")
    for k, v in stats.branches.items():
        print("%s\t %d" % (k, v))

    print("\nPlatform usage:")
    for k, v in stats.platforms.items():
        print("%s\t %d" % (k, v))

    print("\nPlatform+Branch usage:")
    for k, v in stats.platform_branch.items():
        print("%s\t %d" % (k, v))

    print("\nInstall platform breakdown:")
    for k, v in stats.install_platforms.items():
        print("%s\t %d" % (k, v))


def stats_to_dict(stats: Stats) -> dict:
    return {
        "installations_total": stats.installations_total,
        "installations_raw_total": stats.installations_raw_total,
        "unique_installations_tracked": len(stats.installs_tracked_tokens),
        "unique_installations_untracked_ip_proxy": len(stats.installs_untracked_ips),
        "installs_by_date": dict(stats.installs_by_date),
        "installs_unique_by_date": dict(stats.installs_unique_by_date),
        "install_platforms": dict(stats.install_platforms),
        "installs_new_by_date": dict(stats.installs_new_by_date),
        "installs_returning_by_date": dict(stats.installs_returning_by_date),
        "startups_total": len(stats.startups_seen),
        "startups_by_date": dict(stats.startups_by_date),
        "unique_ips": len(stats.unique_ips),
        "unique_tokens": len(stats.unique_tokens),
        "startups_by_token_month": dict(stats.startups_by_token_month),
        "branches": dict(stats.branches),
        "platforms": dict(stats.platforms),
        "platform_branch": dict(stats.platform_branch),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--dir",
        action="append",
        dest="dirs",
        default=None,
        help="Directory containing log files. May be given multiple times. Default: ./test/",
    )
    parser.add_argument(
        "--pattern",
        default=".log",
        help="Substring log filenames must contain to be processed (default: '.log')",
    )
    parser.add_argument(
        "--json",
        metavar="PATH",
        help="Also write a machine-readable summary to this JSON file.",
    )
    args = parser.parse_args()

    dirs = args.dirs or ["./test/"]
    stats = Stats()

    for d in dirs:
        directory = Path(d)
        if not directory.is_dir():
            print(f"Skipping missing directory: {directory}", file=sys.stderr)
            continue
        files = gather_log_files(directory, args.pattern)
        for f in files:
            n_installs, n_unique_ips = process_file(f, stats)
            print("For log: %s" % f)
            print("Raw install-download requests in this file: %d" % n_installs)
            print("Unique installing IPs in this file: %d" % n_unique_ips)

    print_report(stats)

    if args.json:
        Path(args.json).write_text(json.dumps(stats_to_dict(stats), indent=2))
        print(f"\nWrote JSON summary to {args.json}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())