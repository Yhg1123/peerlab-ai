import argparse
from datetime import datetime
import json
from pathlib import Path
import sys

from .client import APIError, clients
from .experiment import load_cases, run_experiment
from .report import export_report
from .datasets import audit_cases, generate_cases, write_dataset


def positive(value):
    n = int(value)
    if n < 1:
        raise argparse.ArgumentTypeError("Must be at least 1")
    return n


def main(argv=None):
    parser = argparse.ArgumentParser(description="PeerLab — DeepSeek × Kimi 三组对照实验")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor", help="Check keys and list models (no chat calls)")
    sub.add_parser("cases", help="Show bundled tasks")
    generate = sub.add_parser("generate", help="Generate exact-arithmetic tasks without API calls")
    generate.add_argument("--family", choices=("bayes", "macro_f1"), default="bayes")
    generate.add_argument("--count", type=positive, default=6)
    generate.add_argument("--seed", type=int, default=42)
    generate.add_argument("--output", type=Path, required=True)
    verify = sub.add_parser("verify-dataset", help="Audit dataset schema and generated reference answers offline")
    verify.add_argument("dataset", type=Path)
    run = sub.add_parser("run", help="Run a paid, bounded experiment")
    run.add_argument("--dataset", type=Path)
    run.add_argument("--limit", type=positive, default=3)
    run.add_argument("--repeats", type=positive, default=1)
    run.add_argument("--seed", type=int, default=42)
    run.add_argument("--max-calls", type=positive, default=30)
    run.add_argument("--max-tokens", type=positive, default=700)
    run.add_argument("--timeout", type=positive, default=90)
    run.add_argument("--output", type=Path)
    report = sub.add_parser("report", help="Regenerate HTML / CSV / Markdown without API calls")
    report.add_argument("run_json", type=Path)
    report.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "generate":
            data = generate_cases(args.family, args.count, args.seed)
            write_dataset(args.output, data)
            print(json.dumps(audit_cases(data), ensure_ascii=False))
            print(f"Dataset: {args.output.resolve()}")
        elif args.command == "verify-dataset":
            print(json.dumps(audit_cases(load_cases(args.dataset)), ensure_ascii=False))
        elif args.command == "cases":
            for case in load_cases():
                print(f"{case['id']:24} {case['category']} · {case['title']}")
        elif args.command == "doctor":
            failed = False
            for c in clients():
                try:
                    models = c.models()
                    print(f"{c.name}: configured={c.model}; available={', '.join(models)}")
                    if c.model not in models:
                        failed = True
                        print(f"  Set {c.name.upper()}_MODEL to a supported non-thinking model.")
                except APIError as exc:
                    failed = True
                    print(f"{c.name}: {exc}")
            return int(failed)
        elif args.command == "report":
            data = json.loads(args.run_json.read_text(encoding="utf-8"))
            dest = args.output or args.run_json.parent
            export_report(data, dest)
            print(f"Report: {(dest / 'report.html').resolve()}")
        else:
            cases = load_cases(args.dataset)[:args.limit]
            planned = len(cases) * args.repeats * 10
            if planned > args.max_calls:
                raise ValueError(f"Planned {planned} calls exceeds --max-calls={args.max_calls}. No API requests sent.")
            providers = clients(args.max_tokens, args.timeout)
            for c in providers:
                if c.model not in c.models():
                    raise ValueError(f"{c.name}: configured model {c.model} unavailable; run doctor. No chat calls sent.")
            dest = args.output or Path("runs") / datetime.now().strftime("%Y%m%d-%H%M%S-%f")
            print(f"Plan: {planned} calls; max {args.max_tokens} output tokens/call; no automatic retries.")
            data = run_experiment(providers, cases, dest, repeats=args.repeats, seed=args.seed, max_calls=args.max_calls)
            export_report(data, dest)
            print(f"Status: {data['status']}\nReport: {(dest / 'report.html').resolve()}")
            return 0 if data["status"] == "complete" else 2
    except (APIError, ValueError, OSError, KeyError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
