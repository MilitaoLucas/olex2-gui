#!/usr/bin/python3
"""
This updates Olex2 HTML.
"""
import sys

target = "/tmp/olexcmd"


def update(target: str = target) -> None:
    with open(target, "w") as f:
        f.write("html.Update")


if __name__ == "__main__":
    args = sys.argv
    if len(args) > 1:
        target = args[1]
    update(target)