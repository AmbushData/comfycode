"""CLI entry point: ``python -m comfycode <workflow.json>``

Reads a ComfyUI workflow JSON file and prints the equivalent Python code.

Usage::

    python -m comfycode path/to/workflow.json
    python -m comfycode path/to/workflow.json -o output.py
"""

import argparse
import json
import sys

from comfycode.converter import convert


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="python -m comfycode",
        description="Convert a ComfyUI workflow JSON file to Python code.",
    )
    parser.add_argument("workflow", help="Path to the ComfyUI workflow JSON file.")
    parser.add_argument(
        "-o",
        "--output",
        default="-",
        help="Output file path. Defaults to stdout (-).",
    )
    args = parser.parse_args()

    with open(args.workflow, encoding="utf-8") as f:
        workflow = json.load(f)

    code = convert(workflow)

    if args.output == "-":
        sys.stdout.write(code)
    else:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(code)


if __name__ == "__main__":
    main()
