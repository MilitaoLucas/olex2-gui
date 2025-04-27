#!/bin/env python
from subprocess import run
branch = [
    "origin/1.1",
    "origin/1.2",
    "origin/1.3",
    "origin/1.5",
    "origin/1.5-ac6",
    "origin/Python26",
    "origin/cctbx-dev",
    "origin/dev",
    "origin/gui-dev",
    "origin/hp01",
    "origin/master",
    "origin/py3",
    "origin/rb-dev",
    "origin/tags/1.1.0",
    "origin/tags/1.1.1",
    "origin/tags/1.1.2",
    "origin/tags/1.1.3",
    "origin/tags/1.1.4",
    "origin/tags/1.1.5",
    "origin/tags/1.2.0",
    "origin/tags/1.2.1",
    "origin/tags/1.2.2",
    "origin/tags/1.2.3",
    "origin/tags/1.2.5",
    "origin/tags/1.2.6",
    "origin/tags/1.2.7",
    "origin/tags/1.2.8",
    "origin/tags/1.3"
]
for b in branch:
    name = b.split("/")[-1]
    if "tags" not in b:
        run(f"git checkout -b {name} {b}".split()) 
    else:
        run(f"git checkout -b tag_{name} {b}".split())
        run(f"git checkout master".split())
        run(f"git tag v{name} tag_{name}".split())
        run(f"git branch -D tag_{name}".split())





