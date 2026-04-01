"""Batch memory checker entrypoint."""
from __future__ import annotations

import argparse
import os

from batchmemorycheckerlib.batch_manager import run_batch_mode, check_batch_statuses
from batchmemorycheckerlib.memory_loader import list_memory_files
from shared.logging_config import setup_logging
from batchmemorycheckerlib.constants import (
    DEFAULT_LANGUAGE,
    DEFAULT_MEMORY_DIR,
    DEFAULT_RESULTS_DIR,
    DEFAULT_BATCH_MAX_MB,
    DEFAULT_BATCH_MAX_RECORDS,
    DEFAULT_BATCH_POLL_INTERVAL,
    DEFAULT_MAX_POLL_ITERATIONS,
    DEFAULT_MODEL_KEY
)


def _build_parser() -> argparse.ArgumentParser:
    supported_files = [os.path.basename(p) for p in list_memory_files(str(DEFAULT_MEMORY_DIR))]
    if supported_files:
        supported_text = "Supported memory files:\n  " + "\n  ".join(supported_files)
    else:
        supported_text = "Supported memory files: none found in memory dir."

    parser = argparse.ArgumentParser(
        description="Batch memory checker",
        epilog=supported_text,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--memory-dir", default=DEFAULT_MEMORY_DIR)
    parser.add_argument("--results-dir", default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--language", default=DEFAULT_LANGUAGE)
    parser.add_argument("--model-key", default=DEFAULT_MODEL_KEY)
    parser.add_argument("--max-records", type=int, default=DEFAULT_BATCH_MAX_RECORDS)
    parser.add_argument("--max-batch-mb", type=int, default=DEFAULT_BATCH_MAX_MB)
    parser.add_argument("--poll-interval", type=int, default=DEFAULT_BATCH_POLL_INTERVAL)
    parser.add_argument("--max-poll", type=int, default=DEFAULT_MAX_POLL_ITERATIONS)
    parser.add_argument("--no-wait", action="store_true")
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--memory-file", action="append", default=[],
                        help="Limit to specific memory file(s), e.g. ProductTypeMemory_CS.csv")
    parser.add_argument("--debug", action="store_true")
    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    setup_logging(debug=args.debug, log_file="batchmemorychecker/batch_state/logfile.log")

    if args.status:
        for line in check_batch_statuses():
            print(line)
        return

    wait_limit = 0 if args.no_wait else args.max_poll

    run_batch_mode(
        memory_dir=args.memory_dir,
        results_dir=args.results_dir,
        language=args.language,
        model_key=args.model_key,
        max_records=args.max_records,
        max_batch_mb=args.max_batch_mb,
        poll_interval=args.poll_interval,
        wait_timeout=wait_limit,
        memory_files=args.memory_file if args.memory_file else None
    )


if __name__ == "__main__":
    main()
