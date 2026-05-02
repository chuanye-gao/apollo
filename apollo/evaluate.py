from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from apollo.router import Router


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset", help="JSONL dataset path")
    parser.add_argument("--tools", default=None)
    parser.add_argument("--embedding", choices=["bge", "hash"], default="bge")
    parser.add_argument("--llm", choices=["openai", "dry-run"], default="openai")
    args = parser.parse_args()

    router = Router.for_modes(embedding=args.embedding, llm=args.llm, tools_path=args.tools)
    rows = [json.loads(line) for line in Path(args.dataset).read_text(encoding="utf-8").splitlines() if line.strip()]
    correct = 0
    tp = fp = fn = 0
    for row in rows:
        result = router.route(row["query"]).to_dict()
        if result["tool_code"] == row["tool_code"]:
            correct += 1
        expected_args = row.get("arguments") or {}
        actual_args = result.get("arguments") or {}
        row_tp, row_fp, row_fn = _slot_counts(expected_args, actual_args)
        tp += row_tp
        fp += row_fp
        fn += row_fn

    accuracy = correct / len(rows) if rows else 0.0
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    slot_f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    print(json.dumps({"tool_code_accuracy": accuracy, "slot_f1": slot_f1}, ensure_ascii=False, indent=2))


def _slot_counts(expected: dict[str, Any], actual: dict[str, Any]) -> tuple[int, int, int]:
    expected_items = {(key, str(value)) for key, value in expected.items()}
    actual_items = {(key, str(value)) for key, value in actual.items()}
    return (
        len(expected_items & actual_items),
        len(actual_items - expected_items),
        len(expected_items - actual_items),
    )


if __name__ == "__main__":
    main()
