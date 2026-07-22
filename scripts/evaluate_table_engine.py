"""运行复杂表格任务金标评测集。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from docnexus.ai.table_engine.evaluation import evaluate_golden_set


def main() -> None:
    parser = argparse.ArgumentParser(description="运行 Any2table 复杂任务金标评测")
    parser.add_argument(
        "--fixture",
        default="backend/tests/fixtures/evaluation/complex_tasks.json",
        help="金标评测 JSON 路径",
    )
    args = parser.parse_args()
    summary = evaluate_golden_set(Path(args.fixture))
    print(json.dumps(summary.to_dict(), ensure_ascii=False, indent=2))
    if summary.passed_count != summary.case_count:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
