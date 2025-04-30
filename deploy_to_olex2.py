#!/usr/bin/env python
"""
This script deploys the Olex2-gui to the Olex2 application directory.
"""
import os
import shutil
import argparse

def main(olex2_path: str, run: bool, start_script: str) -> None:
    print(f"Deploying to {olex2_path}")
    temp = os.listdir()
    itens = temp.copy()
    for i in temp:
        if i.endswith(".docx") or i.endswith(".md") or i.startswith(".") or i.endswith("txt"):
            itens.remove(i)

    print(itens)
    for i in itens:
        if os.path.isdir(i):
            shutil.copytree(i, os.path.join(olex2_path, i), dirs_exist_ok=True)
        else:
            shutil.copy2(i, os.path.join(olex2_path, i))
    
    if run:
        from launch_olex2 import launch_olex
        launch_olex(os.path.join(olex2_path, start_script))
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Sync olex2-gui changes to Olex2."
    )
    parser.add_argument(
        "olex2_path",
        help="The root path containing olex2",
    )
    parser.add_argument("-r", "--run", type=bool, default=False)
    parser.add_argument("-sc", "--start_script", type=str, default="start")
    args = parser.parse_args()
    main(args.olex2_path, args.run, args.start_script)