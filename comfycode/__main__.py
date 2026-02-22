"""CLI entry point: ``python -m comfycode``

Commands:
    convert — Convert a ComfyUI workflow JSON file to Python code
    export  — Export a Python workflow module to prompt JSON

Usage::

    # Convert JSON to Python
    python -m comfycode convert path/to/workflow.json
    python -m comfycode convert path/to/workflow.json -o output.py

    # Export Python to JSON (requires create_workflow() function)
    python -m comfycode export path/to/workflow.py
    python -m comfycode export path/to/workflow.py -o output.json

    # Backward compatible: bare workflow.json defaults to convert
    python -m comfycode path/to/workflow.json
"""

import argparse
import json
import sys

from comfycode.converter import convert
from comfycode.export import export_from_module, ExportError


def cmd_convert(args: argparse.Namespace) -> int:
    """Handle the convert command."""
    try:
        with open(args.workflow, encoding="utf-8") as f:
            workflow = json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found: {args.workflow}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {args.workflow}: {e}", file=sys.stderr)
        return 1

    code = convert(workflow)

    if args.output == "-":
        sys.stdout.write(code)
    else:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(code)
    
    return 0


def cmd_export(args: argparse.Namespace) -> int:
    """Handle the export command."""
    try:
        prompt = export_from_module(args.module)
    except ExportError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    output = json.dumps(prompt, indent=2)

    if args.output == "-":
        sys.stdout.write(output)
        sys.stdout.write("\n")
    else:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
            f.write("\n")
    
    return 0


def main() -> int:
    # Check for backward compatibility: if first arg is not a known subcommand
    # and looks like a file path, treat it as legacy convert mode
    if len(sys.argv) > 1 and sys.argv[1] not in ("-h", "--help", "convert", "export"):
        # Legacy mode: first positional arg is the workflow file
        legacy_parser = argparse.ArgumentParser(
            prog="python -m comfycode",
            description="Convert a ComfyUI workflow JSON file to Python code.",
        )
        legacy_parser.add_argument(
            "workflow",
            help="Path to the ComfyUI workflow JSON file.",
        )
        legacy_parser.add_argument(
            "-o", "--output",
            default="-",
            help="Output file path. Defaults to stdout (-).",
        )
        args = legacy_parser.parse_args()
        return cmd_convert(args)
    
    # Modern subcommand mode
    parser = argparse.ArgumentParser(
        prog="python -m comfycode",
        description="ComfyCode CLI — Convert between ComfyUI workflows and Python code.",
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Convert subcommand
    convert_parser = subparsers.add_parser(
        "convert",
        help="Convert a ComfyUI workflow JSON file to Python code.",
    )
    convert_parser.add_argument(
        "workflow",
        help="Path to the ComfyUI workflow JSON file.",
    )
    convert_parser.add_argument(
        "-o", "--output",
        default="-",
        help="Output file path. Defaults to stdout (-).",
    )
    convert_parser.set_defaults(func=cmd_convert)
    
    # Export subcommand
    export_parser = subparsers.add_parser(
        "export",
        help="Export a Python workflow module to prompt JSON.",
    )
    export_parser.add_argument(
        "module",
        help="Path to the Python workflow module (must define create_workflow()).",
    )
    export_parser.add_argument(
        "-o", "--output",
        default="-",
        help="Output file path. Defaults to stdout (-).",
    )
    export_parser.set_defaults(func=cmd_export)
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        return 0
    
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
