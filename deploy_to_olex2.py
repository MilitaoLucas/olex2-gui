#!/usr/bin/env python
"""
This script deploys the Olex2-gui to the Olex2 application directory.
"""
import os
import shutil
import argparse

def main(olex2_path: str) -> None:
    temp = os.listdir()
    itens = temp.copy()
    for i in temp:
        if i.endswith(".docx") or i.endswith(".md") or i.startswith(".") or i.endswith("txt"):
            itens.remove(i)

    for i in itens:
        if os.path.isdir(i):
            shutil.copytree(i, os.path.join(olex2_path, i), dirs_exist_ok=True)
        else:
            shutil.copy2(i, os.path.join(olex2_path, i))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Sync olex2-gui changes to Olex2."
    )
    parser.add_argument(
        "olex2_path",
        help="The root path containing olex2",
    )
    args = parser.parse_args()

    main(args.olex2_path)