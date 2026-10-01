"""Command-line interface for OfferSleuth."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import analyze
from .render import render_json, render_text

PACKAGE_ROOT = Path(__file__).resolve().parent.parent
DEMO_DIR = PACKAGE_ROOT / "demo_data" / "sample_jds"
RESUME_FILE = PACKAGE_ROOT / "demo_data" / "sample_resume.txt"


def _load_resume(args: argparse.Namespace) -> list[str]:
    if args.no_resume:
        return []
    target = args.resume or RESUME_FILE
    if not target.exists():
        return []
    return [
        line.strip(" -•\t")
        for line in target.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def cmd_demo(args: argparse.Namespace) -> int:
    """Analyze every bundled sample JD against the bundled sample resume."""
    which = (args.which or "all").lower()
    files = sorted(DEMO_DIR.glob("*.md"))
    if which != "all":
        files = [f for f in files if f.stem == which]
        if not files:
            sys.exit(
                f"error: no bundled sample named '{args.which}'. "
                "Try: all, good, mediocre, scammy."
            )
    resume = _load_resume(args)
    for jd_file in files:
        report = analyze(
            jd_file.read_text(encoding="utf-8"),
            title=jd_file.stem.replace("_", " ").title() + " (sample)",
            resume_bullets=resume,
        )
        print(render_text(report) if not args.json else render_json(report))
        print()
    return 0


def cmd_analyze(args: argparse.Namespace) -> int:
    if args.jd_text:
        title, text = "Pasted job description", args.jd_text
    elif args.stdin:
        title, text = "Job description (stdin)", sys.stdin.read()
    elif args.jd_file:
        path = Path(args.jd_file)
        if not path.exists():
            sys.exit(f"error: file not found: {args.jd_file}")
        title, text = path.stem.replace("_", " ").title(), path.read_text(encoding="utf-8")
    else:
        sys.exit("error: provide a JD file path, --jd \"...\" text, or --stdin.")

    resume = _load_resume(args)
    report = analyze(text, title=title, resume_bullets=resume)
    print(render_text(report) if not args.json else render_json(report))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="offersleuth",
        description=(
            "OfferSleuth — job-description analyzer: red flags, "
            "salary sanity-checks and tailored resume bullets."
        ),
    )
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--resume", type=Path, default=None,
        help="Resume bullets file (one per line). Defaults to the bundled sample.",
    )
    common.add_argument("--no-resume", action="store_true", help="Skip resume tailoring.")
    common.add_argument("--json", action="store_true", help="Emit JSON instead of the terminal report.")

    sub = parser.add_subparsers(dest="command", metavar="command")

    demo = sub.add_parser(
        "demo", parents=[common],
        help="Run the end-to-end demo on bundled sample JDs.",
    )
    demo.add_argument("which", nargs="?", default="all", help="all | good | mediocre | scammy")
    demo.set_defaults(func=cmd_demo)

    ana = sub.add_parser(
        "analyze", parents=[common],
        help="Analyze a JD from a file, pasted text, or stdin.",
    )
    ana.add_argument("jd_file", nargs="?", default=None, help="Path to a JD text/markdown file.")
    ana.add_argument("--jd", dest="jd_text", default=None, help="Paste the JD text directly.")
    ana.add_argument("--stdin", action="store_true", help="Read the JD from stdin.")
    ana.set_defaults(func=cmd_analyze)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    argv = list(sys.argv[1:] if argv is None else argv)
    # `offersleuth <file>` is shorthand for `offersleuth analyze <file>`.
    if argv and argv[0] not in ("demo", "analyze", "-h", "--help"):
        argv = ["analyze"] + argv
    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help()
        return 2
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
