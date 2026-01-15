#!/usr/bin/env python3
"""
Run status helpers: call `waif in-progress --json` or `bs show <id> --json` and print parsed JSON
This script is intended to be used by the status skill to run commands reliably and return JSON output.
"""

import sys
import json
import subprocess


def run_cmd(cmd):
    try:
        out = subprocess.check_output(
            cmd, stderr=subprocess.STDOUT, shell=True, text=True
        )
        return out
    except subprocess.CalledProcessError as e:
        print(
            json.dumps(
                {
                    "error": True,
                    "cmd": cmd,
                    "returncode": e.returncode,
                    "output": e.output,
                }
            )
        )
        sys.exit(1)


def main(argv):
    if len(argv) < 2:
        print(
            json.dumps(
                {"error": True, "message": "usage: run_status.py [waif|bs] [args...]"}
            )
        )
        sys.exit(2)
    tool = argv[1]
    if tool == "waif":
        cmd = "waif in-progress --json"
    elif tool == "bs":
        if len(argv) < 3:
            print(json.dumps({"error": True, "message": "missing bead id for bs"}))
            sys.exit(2)
        bead = argv[2]
        cmd = f"bs show {bead} --json"
    else:
        print(json.dumps({"error": True, "message": f"unknown tool {tool}"}))
        sys.exit(2)
    out = run_cmd(cmd)
    try:
        parsed = json.loads(out)
        print(json.dumps(parsed))
    except json.JSONDecodeError:
        print(
            json.dumps({"error": True, "message": "failed to parse json", "raw": out})
        )
        sys.exit(1)


if __name__ == "__main__":
    main(sys.argv)
